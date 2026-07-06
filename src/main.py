"""TripAgent 入口 — Streamlit 对话式交互界面（推理可视化 · 流式输出 · 多轮记忆 · 四象限布局）"""

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


# ========== 可视化辅助函数 ==========

def _has_folium():
    """检测 folium 和 streamlit-folium 是否可用"""
    try:
        import folium
        from streamlit_folium import st_folium
        return True
    except ImportError:
        return False


def _has_pandas():
    """检测 pandas 是否可用"""
    try:
        import pandas as pd
        return True
    except ImportError:
        return False


def render_route_map(trace):
    """从工具调用 trace 中提取路线数据，用 folium 渲染"""
    try:
        from tools.result_parser import extract_route_spots
    except ImportError:
        from src.tools.result_parser import extract_route_spots

    spots = extract_route_spots(trace)
    if not spots:
        st.info("发送旅行需求后，路线地图将在此显示")
        return

    if not _has_folium():
        st.warning("需要安装 folium 和 streamlit-folium 来显示地图")
        _display_fallback_route(spots)
        return

    import folium
    from streamlit_folium import st_folium

    center = [spots[0]["lat"], spots[0]["lng"]]
    m = folium.Map(location=center, zoom_start=13, tiles="OpenStreetMap")

    # 用项目配色绘制 Marker 和连线
    colors = ["#12B7F5", "#0E9FD6", "#07C160"]  # primary → primary-hover → success
    prev = None
    for i, spot in enumerate(spots):
        color = colors[i % len(colors)]
        # Marker：编号圆点
        folium.CircleMarker(
            location=[spot["lat"], spot["lng"]],
            radius=8,
            popup=f"<b>{i+1}. {spot['name']}</b>",
            color=color,
            fill=True,
            fill_color=color,
            fill_opacity=0.8,
        ).add_to(m)
        # 数字标签
        folium.Marker(
            location=[spot["lat"], spot["lng"]],
            icon=folium.DivIcon(
                html=f'<div style="color:white;font-weight:bold;font-size:12px">{i+1}</div>'
            ),
        ).add_to(m)

        if prev:
            folium.PolyLine(
                locations=[[prev["lat"], prev["lng"]], [spot["lat"], spot["lng"]]],
                color=color,
                weight=3,
                dash_array="5,5",
                opacity=0.7,
            ).add_to(m)
        prev = spot

    st_folium(m, height=350, use_container_width=True)


def _display_fallback_route(spots):
    """无 folium 时的纯文本路线展示"""
    for spot in spots:
        st.markdown(
            f"**{spot['order']}.** {spot['name']} "
            f"({spot['lat']:.4f}, {spot['lng']:.4f})"
        )
        if spot['order'] < len(spots):
            st.markdown("&nbsp;&nbsp;&nbsp;&nbsp;⬇️")


def render_ranking_table(trace):
    """从工具调用 trace 中提取餐厅数据，渲染排名表格"""
    try:
        from tools.result_parser import extract_restaurant_items
    except ImportError:
        from src.tools.result_parser import extract_restaurant_items

    items = extract_restaurant_items(trace)
    if not items:
        st.info("发送旅行需求后，餐厅排行榜将在此显示")
        return

    if not _has_pandas():
        _display_fallback_ranking(items)
        return

    import pandas as pd

    df = pd.DataFrame(items)
    # 选择展示列
    display_cols = {
        "rank": "排名",
        "name": "餐厅",
        "rating": "评分",
        "price_per_person": "人均(¥)",
        "distance_m": "距离(m)",
        "type": "类型",
    }
    available_cols = {k: v for k, v in display_cols.items() if k in df.columns}
    df_display = df[list(available_cols.keys())].rename(columns=available_cols)

    # 条件着色：🥇金色、🥈银色、🥉铜色
    def highlight_rank(val):
        if val == 1:
            return "background-color: #FFF7E6; font-weight: bold"
        elif val == 2:
            return "background-color: #F0F1F3; font-weight: bold"
        elif val == 3:
            return "background-color: #FFF0E0; font-weight: bold"
        return ""

    styled = df_display.style.map(highlight_rank, subset=["排名"])
    st.dataframe(styled, height=350, use_container_width=True, hide_index=True)


def _display_fallback_ranking(items):
    """无 pandas 时的纯文本排名展示"""
    rank_emoji = {1: "🥇", 2: "🥈", 3: "🥉"}
    for item in items:
        emoji = rank_emoji.get(item.get("rank", 99), "·")
        st.markdown(
            f"{emoji} **{item.get('name', '未知')}** | "
            f"⭐{item.get('rating', 0)} | "
            f"¥{item.get('price_per_person', 0)}/人 | "
            f"📏{item.get('distance_m', 0)}m"
        )


def render_hotel_ranking(trace):
    """从工具调用 trace 中提取酒店数据，渲染酒店排行"""
    try:
        from tools.result_parser import extract_hotel_items
    except ImportError:
        from src.tools.result_parser import extract_hotel_items

    items = extract_hotel_items(trace)
    if not items:
        st.info("发送旅行需求后，酒店推荐将在此显示")
        return

    if not _has_pandas():
        for item in items:
            st.markdown(
                f"**{item.get('rank', '·')}.** {item.get('name', '未知')} | "
                f"{item.get('type', '')} | "
                f"¥{item.get('price_per_night', 0)}/晚 | "
                f"⭐{item.get('rating', 0)}"
            )
        return

    import pandas as pd

    df = pd.DataFrame(items)
    display_cols = {
        "rank": "排名",
        "name": "酒店",
        "rating": "评分",
        "price_per_night": "每晚(¥)",
        "distance_m": "距离(m)",
        "type": "类型",
        "feature": "特点",
    }
    available_cols = {k: v for k, v in display_cols.items() if k in df.columns}
    df_display = df[list(available_cols.keys())].rename(columns=available_cols)

    def highlight_rank(val):
        if val == 1:
            return "background-color: #FFF7E6; font-weight: bold"
        elif val == 2:
            return "background-color: #F0F1F3; font-weight: bold"
        elif val == 3:
            return "background-color: #FFF0E0; font-weight: bold"
        return ""

    styled = df_display.style.map(highlight_rank, subset=["排名"])
    st.dataframe(styled, height=350, use_container_width=True, hide_index=True)


def render_weather_card(trace):
    """从 trace 中提取天气数据展示"""
    weather_data = None
    for step in trace:
        if step.get("tool") == "get_weather" and "output" in step:
            weather_data = step["output"]
            break

    if weather_data:
        with st.expander("🌤️ 天气详情", expanded=False):
            st.markdown(weather_data)


# ========== 四象限布局 ==========

# 上排：对话 + 推理
col_tl, col_tr = st.columns([3, 2])

with col_tl:
    st.title("✈️ TripAgent · AI 旅行规划助手")
    st.caption("用自然语言描述旅行需求，智能助手自主调用多工具、多步推理，为你生成完整行程方案。")

    # 渲染历史消息（使用容器限制高度，避免挤占底部空间）
    chat_container = st.container(height=350)
    with chat_container:
        if st.session_state.messages:
            for msg in st.session_state.messages:
                with st.chat_message(msg["role"]):
                    st.markdown(msg["content"])
        else:
            st.info("👆 在下方输入框中描述你的旅行需求")

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

def _step_summary(step: dict) -> str:
    """生成推理步骤的一行摘要，折叠状态下也能快速了解全链路"""
    action = step.get("action", "")
    if "调用工具" in action:
        tool = step.get("tool", "未知")
        args = step.get("input", {})
        key_parts = []
        for k, v in args.items():
            if isinstance(v, str) and len(v) < 30:
                key_parts.append(f"{k}={v}")
        arg_str = ", ".join(key_parts[:2]) if key_parts else ""
        return f"🔧 {tool}({arg_str})"
    elif "综合回复" in action:
        thought = step.get("thought", "")
        return f"💬 {thought[:80]}{'...' if len(thought) > 80 else ''}"
    elif "出错" in action:
        return f"❌ {step.get('thought', '')[:80]}"
    return action


with col_tr:
    st.subheader("🔍 推理过程追踪")
    st.caption("智能助手每一步决策透明可见，点击展开查看详情。")

    if st.session_state.trace:
        # 统计摘要
        tool_count = len([s for s in st.session_state.trace if "调用工具" in s.get("action", "")])
        reply_count = len([s for s in st.session_state.trace if "综合回复" in s.get("action", "")])
        st.caption(f"共 {len(st.session_state.trace)} 步 · 🔧 {tool_count} 次工具调用 · 💬 {reply_count} 次综合回复")

        for step in st.session_state.trace:
            summary = _step_summary(step)
            with st.expander(
                f"第{step['num']}步 {summary}",
                expanded=False  # 全部默认折叠，点击展开
            ):
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

# === 下排：地图 + 排名（使用醒目的彩色容器） ===
st.divider()
st.markdown("### 📊 可视化面板")

col_bl, col_br = st.columns([1, 1])

with col_bl:
    with st.container(border=True):
        st.subheader("🗺️ 路线地图")
        render_route_map(st.session_state.trace)

    # 天气卡片
    with st.container(border=True):
        render_weather_card(st.session_state.trace)
        if not any(s.get("tool") == "get_weather" and "output" in s for s in st.session_state.trace):
            st.caption("🌤️ 天气信息将在规划行程时自动获取")

with col_br:
    with st.container(border=True):
        # 用 tabs 切换餐厅和酒店排名
        tab_restaurant, tab_hotel = st.tabs(["🍜 美食排行榜", "🏨 酒店推荐榜"])

        with tab_restaurant:
            render_ranking_table(st.session_state.trace)

        with tab_hotel:
            render_hotel_ranking(st.session_state.trace)
