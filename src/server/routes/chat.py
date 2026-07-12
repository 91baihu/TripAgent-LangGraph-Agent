"""对话路由 — SSE 流式 & 同步对话

阶段二：注入可选认证 + 设备指纹 + 额度检查 + 消费
阶段三：会话创建/获取 + SSE 过程消息持久化
"""

import json
import uuid
from typing import Optional

from fastapi import APIRouter, Depends, Request
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

# SSE 可选依赖
try:
    from sse_starlette.sse import EventSourceResponse

    SSE_AVAILABLE = True
except ImportError:
    SSE_AVAILABLE = False

from ..schemas.chat import ChatRequest, ChatReply, ErrorResponse
from ..services.agent_service import agent_service, AgentEvent
from ..services.credit_service import credit_service
from ..services.session_service import session_service
from ..middleware import RateLimitGuard, get_device_fingerprint
from ..auth import get_optional_user
from ..database import get_db

router = APIRouter()

# 限流守卫: 每 IP 每分钟最多 30 次请求
chat_rate_guard = RateLimitGuard(max_requests=30, window_seconds=60.0)


async def sse_event_generator_with_persistence(
    messages: list,
    travel_plan: dict,
    request_id: str,
    db: AsyncSession,
    session_id: str,
    user_id: Optional[str],
):
    """SSE 事件生成器 — 将 Agent 事件转为 SSE 格式，并持久化到 chat_messages 表"""
    async for event in agent_service.stream_chat(messages, travel_plan):
        # ── 持久化事件到数据库 ──
        try:
            if event.type == "tool_call":
                await session_service.save_message(
                    db,
                    session_id,
                    role="tool",
                    content="",
                    user_id=user_id,
                    tool_name=event.data.get("tool"),
                    tool_args=event.data.get("args"),
                )
            elif event.type == "tool_result":
                await session_service.update_tool_result(
                    db,
                    session_id,
                    tool_name=event.data.get("tool", ""),
                    result=event.data.get("result", ""),
                )
            elif event.type == "reply":
                await session_service.save_message(
                    db,
                    session_id,
                    role="assistant",
                    content=event.data.get("content", ""),
                    user_id=user_id,
                )
        except Exception:
            # 持久化失败不影响 SSE 输出
            pass

        yield {
            "event": event.type,
            "id": request_id,
            "data": json.dumps(event.data, ensure_ascii=False),
        }


@router.post("/chat/stream", response_model=None)
async def chat_stream(
    request: ChatRequest,
    req: Request,
    _: None = Depends(chat_rate_guard),
    db: AsyncSession = Depends(get_db),
    current_user: Optional[dict] = Depends(get_optional_user),
    device_id: Optional[str] = Depends(get_device_fingerprint),
):
    """流式对话（SSE）— Agent 逐步返回推理过程

    事件类型：
    - tool_call: Agent 调用工具
    - tool_result: 工具返回结果
    - reply: Agent 综合回复
    - geo_data: 可视化数据（路线/排行/天气）
    - error: 错误
    - done: 完成信号
    """
    request_id = getattr(req.state, "request_id", str(uuid.uuid4())[:8])
    user_id = current_user.get("sub") if current_user else None

    # 提取城市信息（从用户最后一条消息推断）
    user_messages = [m for m in request.messages if m.role == "user"]
    last_user_msg = user_messages[-1].content if user_messages else ""
    # 简单提取城市名（后续可用 LLM 更精确提取）
    city = request.travel_plan.get("city") if request.travel_plan else None

    # ① 额度检查
    quota = await credit_service.check_quota(
        db, user_id=user_id, device_fingerprint=device_id
    )

    if not quota.has_quota and quota.is_guest:
        # 游客硬拦截
        return ErrorResponse(
            error="quota_exhausted",
            message=quota.message,
            request_id=request_id,
        )

    # ② 创建/获取会话
    session = await session_service.get_or_create_session(
        db,
        user_id=user_id,
        device_fingerprint=device_id,
        city=city,
        title=last_user_msg[:50] if last_user_msg else "新的旅程",
    )

    # ③ 保存用户消息
    try:
        await session_service.save_message(
            db,
            session.id,
            role="user",
            content=last_user_msg,
            user_id=user_id,
        )
    except Exception:
        pass

    # ④ 消费额度
    await credit_service.consume_quota(
        db,
        user_id=user_id,
        device_fingerprint=device_id,
        session_id=session.id,
    )

    # ⑤ 流式返回（带持久化）
    if not SSE_AVAILABLE:
        # 降级为同步模式
        result = agent_service.chat_sync(
            messages=[m.model_dump() for m in request.messages],
            travel_plan=request.travel_plan,
        )
        # 同步模式下也保存回复
        try:
            await session_service.save_message(
                db,
                session.id,
                role="assistant",
                content=result["reply"],
                user_id=user_id,
            )
        except Exception:
            pass
        return ChatReply(
            reply=result["reply"],
            trace=result.get("trace", []),
            request_id=request_id,
        )

    return EventSourceResponse(
        sse_event_generator_with_persistence(
            messages=[m.model_dump() for m in request.messages],
            travel_plan=request.travel_plan,
            request_id=request_id,
            db=db,
            session_id=session.id,
            user_id=user_id,
        )
    )


@router.post("/chat", response_model=ChatReply)
async def chat_sync(
    request: ChatRequest,
    req: Request,
    _: None = Depends(chat_rate_guard),
    db: AsyncSession = Depends(get_db),
    current_user: Optional[dict] = Depends(get_optional_user),
    device_id: Optional[str] = Depends(get_device_fingerprint),
):
    """同步对话 — 等待 Agent 完整推理后返回"""
    request_id = getattr(req.state, "request_id", str(uuid.uuid4())[:8])
    user_id = current_user.get("sub") if current_user else None

    user_messages = [m for m in request.messages if m.role == "user"]
    last_user_msg = user_messages[-1].content if user_messages else ""
    city = request.travel_plan.get("city") if request.travel_plan else None

    # ① 额度检查
    quota = await credit_service.check_quota(
        db, user_id=user_id, device_fingerprint=device_id
    )
    if not quota.has_quota and quota.is_guest:
        return ChatReply(
            reply=quota.message,
            trace=[],
            request_id=request_id,
        )

    # ② 创建会话
    session = await session_service.get_or_create_session(
        db,
        user_id=user_id,
        device_fingerprint=device_id,
        city=city,
        title=last_user_msg[:50] if last_user_msg else "新的旅程",
    )

    # ③ 保存用户消息
    try:
        await session_service.save_message(
            db, session.id, role="user", content=last_user_msg, user_id=user_id
        )
    except Exception:
        pass

    # ④ 消费额度
    await credit_service.consume_quota(
        db, user_id=user_id, device_fingerprint=device_id, session_id=session.id
    )

    # ⑤ 执行推理
    result = agent_service.chat_sync(
        messages=[m.model_dump() for m in request.messages],
        travel_plan=request.travel_plan,
    )

    # ⑥ 保存回复
    try:
        await session_service.save_message(
            db, session.id, role="assistant", content=result["reply"], user_id=user_id
        )
    except Exception:
        pass

    return ChatReply(
        reply=result["reply"],
        trace=result.get("trace", []),
        request_id=request_id,
    )


@router.get("/chat/health")
async def chat_health():
    """对话服务健康检查"""
    return {
        "service": "chat",
        "llm": "deepseek-chat",
        "tools": [
            "search_attractions",
            "get_weather",
            "plan_route",
            "search_restaurants",
        ],
    }
