"""Agent 状态定义 — LangGraph StateGraph 的状态类型"""

from typing import TypedDict, Annotated, List
from langgraph.graph.message import add_messages
from langchain_core.messages import BaseMessage


class AgentState(TypedDict):
    """Agent 的全局状态，在图的节点间流转"""
    messages: Annotated[List[BaseMessage], add_messages]  # 对话历史（自动追加）
    next_step: str                                          # 下一步路由：continue | end
    travel_plan: dict                                       # 最终输出的旅行计划
