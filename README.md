# ✈️ TripAgent — AI 旅行规划 Agent

基于 **LangGraph** 的多工具调用旅行规划 Agent。用户用自然语言描述需求，Agent 自主调用景点搜索、天气查询、路线规划、美食推荐等工具，多步推理后输出完整旅行方案。

## 🎯 核心亮点

- **LangGraph StateGraph** 驱动的 ReAct 循环（Reasoning + Acting）
- **4 个 LangChain Tool**：景点搜索 · 天气查询 · 路线规划 · 美食推荐
- **推理过程可视化**：Streamlit 侧边栏实时展示每一步推理决策
- **多轮对话记忆**：支持在已有计划上增量修改
- **流式输出**：逐字渲染 Agent 回复，体验流畅

## 🏗️ 架构

```
用户输入："帮我规划3天北京亲子游，预算中等，孩子6岁"
    │
    ▼
┌─────────────────────────────────────────────┐
│              LangGraph Agent                │
│                                             │
│   ┌─────────┐    ┌──────────┐    ┌───────┐ │
│   │ 理解意图 │ → │ 决定调哪个 │ → │ 执行   │ │
│   │ 拆解子任务│   │ 工具       │   │ 工具   │ │
│   └─────────┘    └──────────┘    └───┬───┘ │
│        ↑                              │     │
│        │        ┌──────────┐         │     │
│        └────────│ 判断结果  │←────────┘     │
│                │ 够不够？  │               │
│                └────┬─────┘               │
│                     │ 不够→再调工具        │
│                     │ 够了→综合输出        │
└─────────────────────┼─────────────────────┘
                      ▼
              📋 完整旅行计划
```

## 🔧 Agent 能力

| 工具 | 功能 | 数据来源 |
|------|------|---------|
| `search_attractions` | 搜索景点、获取详细信息 | Mock 数据 / RAG 混合检索 |
| `get_weather` | 查询指定日期+城市天气 | [wttr.in](https://wttr.in) 免费天气 API |
| `plan_route` | 计算两景点间距离/交通方式 | 坐标计算 |
| `search_restaurants` | 搜索附近美食 | Mock 数据 |

## 🚀 快速开始

### 1. 克隆仓库

```bash
git clone <your-repo-url>
cd trip-agent
```

### 2. 安装依赖

```bash
pip install -r requirements.txt
```

### 3. 配置 API Key

编辑 `.env` 文件，填入你的 DeepSeek API Key：

```
DEEPSEEK_API_KEY=sk-your-key-here
```

> 获取 Key：[platform.deepseek.com](https://platform.deepseek.com)

### 4. 启动

```bash
cd src
streamlit run main.py
```

浏览器打开 `http://localhost:8501`，输入旅行需求即可体验。

### 5. 运行测试

```bash
# 运行工具函数测试（不需要 API Key）
pytest tests/test_tools.py -v -k "not AgentIntegration"

# 运行全部测试（需要配置 API Key）
pytest tests/test_tools.py -v
```

## 📁 项目结构

```
trip-agent/
├── requirements.txt
├── .env                        # DEEPSEEK_API_KEY=xxx
├── .gitignore
├── README.md
├── src/
│   ├── main.py                 # Streamlit 入口（含推理可视化）
│   ├── agent/
│   │   ├── __init__.py
│   │   ├── graph.py            # ⭐ LangGraph 核心：构建状态图
│   │   ├── state.py            # Agent 状态定义
│   │   └── prompts.py          # System Prompt
│   ├── tools/
│   │   ├── __init__.py
│   │   ├── attractions.py      # 景点搜索工具
│   │   ├── weather.py          # 天气查询工具
│   │   ├── route.py            # 路线规划工具
│   │   └── restaurants.py      # 美食搜索工具
│   └── rag/                    # RAG 混合检索模块
│       ├── __init__.py
│       ├── retriever.py        # HybridRetriever（BM25 + 向量）
│       └── data/
│           └── attractions.json # 景区知识库
└── tests/
    └── test_tools.py           # 工具函数 & 集成测试
```

## 🧠 推理过程可视化

启动后，界面右侧面板会实时展示 Agent 的推理过程：

- 🔧 **调用了哪个工具**
- 📥 **传入了什么参数**
- 📤 **返回了什么结果**
- 💬 **Agent 如何综合信息输出最终方案**

这对于面试展示和调试优化都非常有价值。

## 🛠️ 技术栈

| 组件 | 技术 |
|------|------|
| Agent 框架 | LangGraph |
| LLM | DeepSeek Chat API |
| 工具定义 | LangChain `@tool` 装饰器 |
| 前端 | Streamlit |
| RAG 检索 | 自研 HybridRetriever |
| 测试 | pytest |

## 📝 简历描述

> **TripAgent — 基于 LangGraph 的多工具调用旅行规划 Agent**
>
> - 设计 LangGraph StateGraph 编排 Agent 的 ReAct 循环：理解意图 → 工具选择 → 工具执行 → 结果判断 → 综合输出
> - 实现 4 个 LangChain Tool，通过 `@tool` 装饰器自动生成 LLM 可理解的 function schema
> - 设计分层 System Prompt（角色定义 + 工作流程 + 输出格式约束 + 注意事项）
> - 使用 Streamlit 搭建对话式 UI，侧边栏实时展示 Agent 推理链路
> - 支持多轮对话记忆和流式输出

## 🔄 后续扩展方向

- [ ] 接入高德/百度地图 API 实现真实路线规划
- [ ] 接入大众点评 API 获取实时餐厅评价
- [ ] 使用真正的 embedding 模型（BGE）升级向量检索
- [ ] 添加 FastAPI 后端，支持移动端调用
- [ ] Token 用量追踪与成本估算

---

*Day 1-10 逐步搭建，每一步都可追溯。*
