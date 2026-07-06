"""TripAgent 入口 — Streamlit 对话式交互界面（推理可视化 · 流式输出 · 多轮记忆）"""

import streamlit as st
from agent.graph import create_agent
from langchain_core.messages import ToolMessage, AIMessage, HumanMessage

st.set_page_config(page_title="TripAgent · AI 旅行规划", page_icon="✈️", layout="wide")

# === 初始化 Session State ===
if "agent" not in st.session_state:
    st.session_state.agent = create_agent()
if "messages" not in st.session_state:
    st.session_state.messages = []
if "trace" not in st.session_state:
    st.session_state.trace = []

# === 左侧：对话区 ===
col_main, col_sidebar = st.columns([3, 2])

with col_main:
    st.title("✈️ TripAgent · AI 旅行规划助手")
    st.caption("用自然语言描述旅行需求，智能助手自主调用多工具、多步推理，为你生成完整行程方案。")

    # 渲染历史消息
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    # 用户输入
    if prompt := st.chat_input("说说你的旅行需求，比如：帮我规划3天北京亲子游"):
        # 添加用户消息
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            # 使用 stream 模式捕获中间步骤
            trace = []
            step_num = 0
            final_reply = ""

            # 构建完整消息历史传入（多轮记忆）
            input_messages = [
                {"role": m["role"], "content": m["content"]}
                for m in st.session_state.messages
            ]

            with st.spinner("🤔 正在为你规划行程，请稍候..."):
                try:
                    for event in st.session_state.agent.stream(
                        {"messages": input_messages,
                         "next_step": "",
                         "travel_plan": st.session_state.get("travel_plan", {})},
                        stream_mode="values"
                    ):
                        if not event.get("messages"):
                            continue
                        last_msg = event["messages"][-1]

                        # 捕获工具调用
                        if isinstance(last_msg, AIMessage) and hasattr(last_msg, "tool_calls") and last_msg.tool_calls:
                            for tc in last_msg.tool_calls:
                                step_num += 1
                                trace.append({
                                    "num": step_num,
                                    "action": "🔧 调用工具",
                                    "tool": tc["name"],
                                    "input": tc["args"]
                                })

                        # 捕获工具返回
                        elif isinstance(last_msg, ToolMessage):
                            if trace:
                                trace[-1]["output"] = last_msg.content[:500]

                        # 捕获最终回复
                        elif isinstance(last_msg, AIMessage) and last_msg.content:
                            step_num += 1
                            trace.append({
                                "num": step_num,
                                "action": "💬 综合回复",
                                "thought": last_msg.content[:300]
                            })
                            final_reply = last_msg.content

                    # 如果没有流式输出，用 invoke 兜底
                    if not final_reply and event.get("messages"):
                        final_msg = event["messages"][-1]
                        final_reply = final_msg.content if hasattr(final_msg, "content") else str(final_msg)

                except Exception as e:
                    final_reply = f"❌ 处理出错：{str(e)}\n\n请检查：\n1. .env 文件中的 DEEPSEEK_API_KEY 是否正确\n2. 网络连接是否正常\n3. DeepSeek API 账户余额是否充足"
                    trace.append({
                        "num": step_num + 1,
                        "action": "❌ 出错",
                        "thought": str(e)[:300]
                    })

            # 保存 trace
            st.session_state.trace = trace
            st.markdown(final_reply)

        # 保存助手回复
        st.session_state.messages.append({"role": "assistant", "content": final_reply})

# === 右侧：推理追踪面板 ===
with col_sidebar:
    st.subheader("🔍 推理过程追踪")
    st.caption("实时展示智能助手每一步推理决策，让 AI 思考透明可见。")

    if st.session_state.trace:
        for step in st.session_state.trace:
            emoji = step["action"].split(" ")[0] if " " in step["action"] else "📌"
            with st.expander(f"{emoji} 第{step['num']}步：{step['action']}", expanded=(step["action"] == "🔧 调用工具")):
                if "调用工具" in step["action"]:
                    st.caption(f"🔨 调用的工具：**{step['tool']}**")
                    st.caption("📥 输入参数：")
                    st.json(step["input"])
                    if "output" in step:
                        st.caption("📤 返回结果：")
                        st.text(step["output"])
                    else:
                        st.caption("⏳ 执行中...")
                elif "综合回复" in step["action"]:
                    st.text(step.get("thought", ""))
                elif "出错" in step["action"]:
                    st.error(step.get("thought", ""))
    else:
        st.info("👆 发送一条消息来观察智能助手的推理过程...")
        st.markdown("""
        **你会看到：**
        - 🧠 智能助手决定调用哪个工具
        - 📥 传入的参数是什么
        - 📤 工具返回了什么结果
        - 💬 智能助手如何综合信息生成最终方案
        """)

    # 底部：状态栏
    st.divider()
    st.caption(f"💬 对话轮次：{len(st.session_state.messages) // 2}")
    st.caption(f"🔧 工具调用次数：{len([s for s in st.session_state.trace if '调用工具' in s.get('action', '')])}")
