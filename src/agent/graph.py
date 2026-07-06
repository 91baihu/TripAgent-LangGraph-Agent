"""LangGraph Agent 核心 — 构建 StateGraph，编排 Agent 的 ReAct 循环"""

from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
from langchain_deepseek import ChatDeepSeek
from langchain_core.messages import SystemMessage
import os
from dotenv import load_dotenv

from .state import AgentState
from .prompts import SYSTEM_PROMPT

# 兼容 Streamlit (运行目录为 src/) 和 FastAPI (包导入) 两种方式
try:
    from ..tools.attractions import search_attractions
    from ..tools.weather import get_weather
    from ..tools.route import plan_route
    from ..tools.restaurants import search_restaurants
except ImportError:
    from tools.attractions import search_attractions
    from tools.weather import get_weather
    from tools.route import plan_route
    from tools.restaurants import search_restaurants

load_dotenv()


def create_agent():
    """创建并编译 LangGraph Agent

    Returns:
        CompiledGraph: 编译后的 Agent 状态图，可直接 invoke/stream
    """
    # 1. 绑定工具到 LLM
    tools = [search_attractions, get_weather, plan_route, search_restaurants]
    llm = ChatDeepSeek(
        model="deepseek-chat",
        api_key=os.getenv("DEEPSEEK_API_KEY"),
        temperature=0.3,
        streaming=True  # 开启流式输出
    )
    llm_with_tools = llm.bind_tools(tools)

    # 2. 定义节点
    def agent_node(state: AgentState):
        """Agent 思考节点：决定下一步做什么"""
        messages = state["messages"]
        # 首次调用时注入 system prompt
        if not any(isinstance(m, SystemMessage) for m in messages):
            messages = [SystemMessage(content=SYSTEM_PROMPT)] + messages

        try:
            response = llm_with_tools.invoke(messages)
        except Exception as e:
            # LLM 调用失败时返回友好提示
            from langchain_core.messages import AIMessage
            response = AIMessage(
                content=f"抱歉，AI 服务调用暂时失败：{str(e)[:200]}\n\n"
                        f"请检查：\n"
                        f"1. .env 文件中的 DEEPSEEK_API_KEY 是否正确\n"
                        f"2. 网络连接是否正常\n"
                        f"3. DeepSeek API 账户余额是否充足"
            )
        return {"messages": [response]}

    tool_node = ToolNode(tools)  # LangGraph 内置工具执行节点

    # 3. 路由函数：判断继续还是结束
    def should_continue(state: AgentState):
        last_message = state["messages"][-1]
        # 如果 LLM 想调工具 → 去 tool_node
        if hasattr(last_message, "tool_calls") and last_message.tool_calls:
            return "tools"
        # 否则结束
        return END

    # 4. 构建图
    workflow = StateGraph(AgentState)
    workflow.add_node("agent", agent_node)
    workflow.add_node("tools", tool_node)

    workflow.set_entry_point("agent")
    workflow.add_conditional_edges("agent", should_continue, {
        "tools": "tools",
        END: END
    })
    workflow.add_edge("tools", "agent")  # 工具结果 → 回到 agent 继续思考

    return workflow.compile()
