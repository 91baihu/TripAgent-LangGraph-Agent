"""Agent 服务层 — 将 LangGraph Agent 封装为无状态服务"""

from typing import AsyncIterator, Dict, Any
from dataclasses import dataclass, field

from langchain_core.messages import AIMessage, ToolMessage, SystemMessage

from ...agent.graph import create_agent
from ...agent.state import AgentState
from ...agent.prompts import SYSTEM_PROMPT


@dataclass
class AgentEvent:
    """Agent 流式事件的标准化结构"""
    type: str          # "tool_call" | "tool_result" | "thinking" | "reply" | "error" | "done"
    data: Dict[str, Any] = field(default_factory=dict)


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
                    yield AgentEvent(
                        type="tool_result",
                        data={
                            "step": step_num,
                            "tool": last_msg.name if hasattr(last_msg, "name") else "unknown",
                            "result": last_msg.content[:500] if last_msg.content else "",
                        },
                    )

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
