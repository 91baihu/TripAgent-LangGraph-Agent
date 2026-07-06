"""Agent 服务层 — 将 LangGraph Agent 封装为无状态服务"""

from typing import AsyncIterator, Dict, Any, Optional
from dataclasses import dataclass, field

from langchain_core.messages import AIMessage, ToolMessage, SystemMessage

try:
    from ...agent.graph import create_agent
    from ...agent.state import AgentState
    from ...agent.prompts import SYSTEM_PROMPT
    from ...tools.result_parser import (
        parse_route_result,
        parse_restaurant_result,
        parse_hotel_result,
    )
except ImportError:
    from agent.graph import create_agent
    from agent.state import AgentState
    from agent.prompts import SYSTEM_PROMPT
    from tools.result_parser import (
        parse_route_result,
        parse_restaurant_result,
        parse_hotel_result,
    )


@dataclass
class AgentEvent:
    """Agent 流式事件的标准化结构"""
    type: str          # "tool_call" | "tool_result" | "thinking" | "reply" | "error" | "done" | "geo_data"
    data: Dict[str, Any] = field(default_factory=dict)


def _build_geo_event(tool_name: str, tool_content: str) -> Optional[AgentEvent]:
    """根据工具名称和返回内容构建 geo_data 事件

    Args:
        tool_name: 工具名称 (plan_route, search_restaurants, search_hotels)
        tool_content: 工具返回的 Markdown 文本

    Returns:
        AgentEvent 或 None（解析失败时）
    """
    if tool_name == "plan_route":
        parsed = parse_route_result(tool_content)
        return AgentEvent(
            type="geo_data",
            data={
                "geo_type": "route",
                "spots": parsed.get("spots", []),
                "distance_km": parsed.get("distance_km", 0),
                "duration_min": parsed.get("duration_min", 0),
                "transport": parsed.get("transport", ""),
            },
        )
    elif tool_name == "search_restaurants":
        parsed = parse_restaurant_result(tool_content)
        items = parsed.get("items", [])
        if items:
            return AgentEvent(
                type="geo_data",
                data={
                    "geo_type": "restaurant_ranking",
                    "city": parsed.get("city", ""),
                    "near_spot": parsed.get("near_spot", ""),
                    "items": items,
                },
            )
    elif tool_name == "search_hotels":
        parsed = parse_hotel_result(tool_content)
        items = parsed.get("items", [])
        if items:
            return AgentEvent(
                type="geo_data",
                data={
                    "geo_type": "hotel_ranking",
                    "city": parsed.get("city", ""),
                    "near_spot": parsed.get("near_spot", ""),
                    "items": items,
                },
            )
    return None


class TravelAgentService:
    """旅行规划 Agent 服务

    封装 LangGraph Agent，提供：
    - 流式推理（SSE）
    - 同步推理（HTTP）
    - 错误处理 & 降级
    """

    def __init__(self):
        self._agent = None

    @property
    def agent(self):
        """延迟初始化 Agent（避免模块导入时连接 LLM）"""
        if self._agent is None:
            self._agent = create_agent()
        return self._agent

    async def stream_chat(
        self,
        messages: list,
        travel_plan: dict = None,
    ) -> AsyncIterator[AgentEvent]:
        """流式对话 — 逐个产出 Agent 推理步骤

        Args:
            messages: 完整的对话历史 [{"role": "user/assistant", "content": "..."}]
            travel_plan: 已有的旅行计划（用于增量修改）

        Yields:
            AgentEvent: 每个推理步骤的标准化事件
        """
        try:
            step_num = 0
            async for event in self.agent.astream(
                {
                    "messages": messages,
                    "next_step": "",
                    "travel_plan": travel_plan or {},
                },
                stream_mode="values",
            ):
                if not event.get("messages"):
                    continue

                last_msg = event["messages"][-1]

                # 工具调用事件
                if (
                    isinstance(last_msg, AIMessage)
                    and hasattr(last_msg, "tool_calls")
                    and last_msg.tool_calls
                ):
                    for tc in last_msg.tool_calls:
                        step_num += 1
                        yield AgentEvent(
                            type="tool_call",
                            data={
                                "step": step_num,
                                "tool": tc["name"],
                                "args": tc["args"],
                            },
                        )

                # 工具返回事件
                elif isinstance(last_msg, ToolMessage):
                    tool_name = last_msg.name if hasattr(last_msg, "name") else "unknown"
                    tool_content = last_msg.content if last_msg.content else ""
                    yield AgentEvent(
                        type="tool_result",
                        data={
                            "step": step_num,
                            "tool": tool_name,
                            "result": tool_content[:500],
                        },
                    )

                    # 解析工具结果，发送 geo_data 事件供前端可视化使用
                    try:
                        geo_event = _build_geo_event(tool_name, tool_content)
                        if geo_event:
                            yield geo_event
                    except Exception:
                        pass  # 解析失败不影响主流程

                # 最终回复事件
                elif isinstance(last_msg, AIMessage) and last_msg.content:
                    step_num += 1
                    yield AgentEvent(
                        type="reply",
                        data={
                            "step": step_num,
                            "content": last_msg.content,
                        },
                    )

            # 完成信号
            yield AgentEvent(type="done", data={"total_steps": step_num})

        except Exception as e:
            yield AgentEvent(
                type="error",
                data={
                    "message": f"Agent 处理出错：{str(e)}",
                    "hint": "请检查 DeepSeek API Key 和网络连接",
                },
            )

    def chat_sync(self, messages: list, travel_plan: dict = None) -> dict:
        """同步对话 — 返回完整结果（非流式）

        Returns:
            {"reply": "...", "trace": [...]}
        """
        try:
            result = self.agent.invoke(
                {
                    "messages": messages,
                    "next_step": "",
                    "travel_plan": travel_plan or {},
                }
            )

            reply = result["messages"][-1].content if result.get("messages") else ""

            # 构建 trace
            trace = []
            for msg in result.get("messages", []):
                if (
                    isinstance(msg, AIMessage)
                    and hasattr(msg, "tool_calls")
                    and msg.tool_calls
                ):
                    for tc in msg.tool_calls:
                        trace.append(
                            {"tool": tc["name"], "args": tc["args"]}
                        )

            return {"reply": reply, "trace": trace}

        except Exception as e:
            return {
                "reply": f"❌ Agent 处理出错：{str(e)}",
                "trace": [],
                "error": str(e),
            }


# 全局单例
agent_service = TravelAgentService()
