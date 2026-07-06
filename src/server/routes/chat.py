"""对话路由 — SSE 流式 & 同步对话"""

import json
import uuid

from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse

# SSE 可选依赖
try:
    from sse_starlette.sse import EventSourceResponse

    SSE_AVAILABLE = True
except ImportError:
    SSE_AVAILABLE = False

from ..schemas.chat import ChatRequest, ChatReply, ErrorResponse
from ..services.agent_service import agent_service, AgentEvent

router = APIRouter()


async def sse_event_generator(messages: list, travel_plan: dict, request_id: str):
    """SSE 事件生成器 — 将 Agent 事件转为 SSE 格式"""
    async for event in agent_service.stream_chat(messages, travel_plan):
        yield {
            "event": event.type,
            "id": request_id,
            "data": json.dumps(event.data, ensure_ascii=False),
        }


@router.post("/chat/stream", response_model=None)
async def chat_stream(request: ChatRequest, req: Request):
    """流式对话（SSE）— Agent 逐步返回推理过程

    事件类型：
    - tool_call: Agent 调用工具
    - tool_result: 工具返回结果
    - reply: Agent 综合回复
    - error: 错误
    - done: 完成信号
    """
    request_id = getattr(req.state, "request_id", str(uuid.uuid4())[:8])

    if not SSE_AVAILABLE:
        # 降级为同步模式
        result = agent_service.chat_sync(
            messages=[m.model_dump() for m in request.messages],
            travel_plan=request.travel_plan,
        )
        return ChatReply(
            reply=result["reply"],
            trace=result.get("trace", []),
            request_id=request_id,
        )

    return EventSourceResponse(
        sse_event_generator(
            messages=[m.model_dump() for m in request.messages],
            travel_plan=request.travel_plan,
            request_id=request_id,
        )
    )


@router.post("/chat", response_model=ChatReply)
async def chat_sync(request: ChatRequest, req: Request):
    """同步对话 — 等待 Agent 完整推理后返回"""
    request_id = getattr(req.state, "request_id", str(uuid.uuid4())[:8])

    result = agent_service.chat_sync(
        messages=[m.model_dump() for m in request.messages],
        travel_plan=request.travel_plan,
    )

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
        "tools": ["search_attractions", "get_weather", "plan_route", "search_restaurants"],
    }
