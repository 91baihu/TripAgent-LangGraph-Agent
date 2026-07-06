# ✈️ TripAgent — AI 旅行规划 Agent

基于 **LangGraph** 的多工具调用旅行规划 Agent。用户用自然语言描述需求，Agent 自主调用景点搜索、天气查询、路线规划、美食推荐等工具，多步推理后输出完整旅行方案。

## 🎯 核心亮点

- **LangGraph StateGraph** 驱动的 ReAct 循环（Reasoning + Acting）
- **4 个 LangChain Tool**：景点搜索 · 天气查询 · 路线规划 · 美食推荐
- **双入口架构**：Streamlit 快速原型 + FastAPI 生产级 API
- **SSE 流式对话**：服务端推送 Agent 每一步推理过程
- **推理过程可视化**：Streamlit 侧边栏实时展示推理决策链路
- **多轮对话记忆**：支持在已有计划上增量修改
- **React 前端**：TypeScript + Vite + Tailwind，现代化移动端 Web 体验
- **Docker 一键部署**：PostgreSQL + Redis + Nginx 反向代理
- **JWT 认证**：注册/登录/刷新令牌，API Key 支持 B2B 调用
- **CI/CD**：GitHub Actions 自动测试 → 构建镜像 → 部署

## 🏗️ 架构

```
                          ┌─────────────────────┐
                          │   LangGraph Agent   │
                          │   (src/agent/)      │
                          │   ReAct 循环        │
                          │   4 Tools           │
                          └────────┬────────────┘
                                   │
                    ┌──────────────┴──────────────┐
                    │                             │
          ┌─────────┴─────────┐       ┌──────────┴──────────┐
          │  Streamlit        │       │  FastAPI 服务器       │
          │  src/main.py      │       │  src/server/main.py  │
          │  :8501 原型 UI    │       │  :8000 生产 API      │
          └───────────────────┘       └──────────┬───────────┘
                                                 │
                     ┌───────────────────────────┼───────────────────┐
                     │                           │                   │
               ┌─────┴─────┐              ┌──────┴──────┐   ┌───────┴───────┐
               │ PostgreSQL│              │   Redis     │   │  React 前端    │
               │ 用户/行程 │              │ 缓存/限流   │   │ Vite :5173    │
               │ 审计日志  │              │ 会话管理    │   │                │
               └───────────┘              └─────────────┘   └────────────────┘
```

## 🔧 Agent 能力

| 工具 | 功能 | 数据来源 |
|------|------|---------|
| `search_attractions` | 搜索景点、获取详细信息 | Mock 数据 / RAG 混合检索 |
| `get_weather` | 查询指定日期+城市天气 | [wttr.in](https://wttr.in) 免费天气 API |
| `plan_route` | 计算两景点间距离/交通方式 | 坐标计算 |
| `search_restaurants` | 搜索附近美食 | Mock 数据 |

## 🚀 快速开始

### 方式一：Docker 部署（推荐）

```bash
# 1. 克隆仓库
git clone <your-repo-url>
cd trip-agent

# 2. 配置环境变量
cp config/.env.example config/dev.env
# 编辑 config/dev.env，填入 DEEPSEEK_API_KEY

# 3. 启动全部服务
make up-dev

# 4. 访问
# API 文档:    http://localhost:8000/api/docs
# Streamlit:  http://localhost:8501
```

### 方式二：本地开发

```bash
# 1. 安装依赖
pip install -r requirements.txt

# 2. 配置 API Key
cp config/.env.example .env
# 编辑 .env，填入 DEEPSEEK_API_KEY=sk-your-key-here

# 3. 启动 Streamlit 原型
cd src && streamlit run main.py
# 浏览器打开 http://localhost:8501

# 4. 或启动 FastAPI 服务器
cd src && uvicorn server.main:app --reload --port 8000
# API 文档: http://localhost:8000/api/docs
```

> 获取 DeepSeek API Key：[platform.deepseek.com](https://platform.deepseek.com)

### 方式三：React 前端

```bash
cd frontend
npm install
npm run dev
# 浏览器打开 http://localhost:5173
```

## 🧪 测试

```bash
# 运行工具函数测试（不需要 API Key）
pytest tests/ -v -k "not AgentIntegration"

# 运行全部测试（需要配置 DEEPSEEK_API_KEY）
pytest tests/ -v

# Docker 中运行测试
make test
```

## 📁 项目结构

```
trip-agent/
├── requirements.txt
├── Makefile                        # 常用命令快捷方式
├── Dockerfile                      # 多阶段构建（python:3.12-slim）
├── docker-compose.yml              # api + postgres + redis + nginx + admin
├── docker/
│   ├── init-db.sql                 # 数据库初始化
│   └── nginx.conf                  # 反向代理配置
├── config/
│   ├── .env.example                # 完整环境变量模板
│   ├── dev.env                     # 开发环境配置
│   └── prod.env                    # 生产环境配置
├── .github/workflows/
│   ├── ci.yml                      # PR 自动检查（lint + test + build）
│   └── cd.yml                      # 自动构建镜像 → 部署
├── src/
│   ├── main.py                     # Streamlit 入口（含推理可视化）
│   ├── agent/
│   │   ├── graph.py                # ⭐ LangGraph 核心：构建状态图
│   │   ├── state.py                # Agent 状态定义
│   │   └── prompts.py              # System Prompt
│   ├── tools/
│   │   ├── attractions.py          # 景点搜索工具
│   │   ├── weather.py              # 天气查询工具
│   │   ├── route.py                # 路线规划工具
│   │   └── restaurants.py          # 美食搜索工具
│   ├── server/                     # FastAPI 生产级后端
│   │   ├── main.py                 # 应用入口（工厂模式）
│   │   ├── auth.py                 # JWT + bcrypt 认证
│   │   ├── models.py               # SQLAlchemy ORM（5张表）
│   │   ├── database.py             # 异步数据库引擎 + 连接池
│   │   ├── cache.py                # Redis 缓存（含内存降级）
│   │   ├── middleware.py           # 熔断器 + 限流器 + 请求ID
│   │   ├── logging.py              # 结构化日志（structlog）
│   │   ├── routes/
│   │   │   ├── chat.py             # SSE 流式对话 / 同步对话
│   │   │   ├── trips.py            # 行程 CRUD + 分享
│   │   │   ├── auth.py             # 注册 / 登录 / 刷新令牌
│   │   │   └── tools.py            # 工具调试接口
│   │   ├── schemas/
│   │   │   ├── chat.py             # ChatRequest / ChatReply
│   │   │   └── trip.py             # TripCreate / TripResponse
│   │   └── services/
│   │       └── agent_service.py    # Agent 封装（SSE流式 + 同步）
│   └── rag/                        # RAG 混合检索模块
│       ├── retriever.py            # HybridRetriever
│       └── data/
│           └── attractions.json    # 景区知识库
├── frontend/                       # React 移动端前端
│   ├── package.json
│   ├── vite.config.ts
│   ├── tailwind.config.ts
│   └── src/
│       ├── main.tsx
│       ├── App.tsx
│       ├── components/             # 通用组件库（Button/Card/Modal/Toast...）
│       ├── features/
│       │   ├── auth/               # 登录注册页
│       │   ├── chat/               # 对话页（SSE 流式）
│       │   ├── trips/              # 行程列表/详情
│       │   └── map/                # 地图视图
│       ├── hooks/                  # useChatStream 等自定义 Hook
│       ├── services/               # API 客户端
│       ├── stores/                 # Zustand 状态管理
│       └── design-tokens/          # 设计令牌（颜色/间距/字体）
└── tests/
    └── test_tools.py               # 工具函数 & Agent 集成测试
```

## 🛠️ 技术栈

| 组件 | 技术 |
|------|------|
| Agent 框架 | LangGraph + LangChain |
| LLM | DeepSeek Chat API |
| API 服务 | FastAPI (async) + SSE 流式推送 |
| 数据库 | PostgreSQL 16 + SQLAlchemy 2.0 (async) |
| 缓存 | Redis 7 (含内存降级) |
| 认证 | JWT (python-jose) + bcrypt |
| 原型 UI | Streamlit |
| Web 前端 | React 18 + TypeScript + Vite + Tailwind CSS |
| RAG 检索 | 自研 HybridRetriever |
| 部署 | Docker Compose + Nginx 反向代理 |
| CI/CD | GitHub Actions (自动测试 → 构建 → 部署) |
| 测试 | pytest + pytest-asyncio |
| 代码质量 | Ruff (lint + format) |

## 🧠 推理过程可视化

启动 Streamlit 后，界面右侧面板会实时展示 Agent 的推理过程：

- 🔧 **调用了哪个工具**
- 📥 **传入了什么参数**
- 📤 **返回了什么结果**
- 💬 **Agent 如何综合信息输出最终方案**

FastAPI 版本通过 SSE（Server-Sent Events）将同样的推理步骤实时推送给前端，事件类型包括 `tool_call` → `tool_result` → `reply` → `done`。

## 📡 API 接口

| 方法 | 路径 | 说明 |
|------|------|------|
| `POST` | `/api/v1/chat/stream` | SSE 流式对话（Agent 逐步推理） |
| `POST` | `/api/v1/chat` | 同步对话（等待完整推理后返回） |
| `POST` | `/api/v1/auth/register` | 用户注册 |
| `POST` | `/api/v1/auth/login` | 用户登录 |
| `POST` | `/api/v1/auth/refresh` | 刷新访问令牌 |
| `GET` | `/api/v1/auth/me` | 获取当前用户信息 |
| `POST` | `/api/v1/trips` | 创建行程 |
| `GET` | `/api/v1/trips` | 行程列表（分页） |
| `GET` | `/api/v1/trips/{id}` | 行程详情 |
| `PATCH` | `/api/v1/trips/{id}` | 更新行程 |
| `DELETE` | `/api/v1/trips/{id}` | 删除行程 |
| `POST` | `/api/v1/trips/{id}/share` | 生成分享链接 |
| `GET` | `/api/v1/tools` | 查看可用工具列表 |
| `POST` | `/api/v1/tools/{name}` | 单独测试某个工具 |
| `GET` | `/health` | 健康检查 |

启动 FastAPI 后访问 `http://localhost:8000/api/docs` 查看完整 Swagger 文档。

## 📝 Makefile 常用命令

` ``bash
make up           # 启动核心服务 (api + db + redis)
make up-dev       # 启动开发环境 (含 Streamlit 管理面板)
make down         # 停止全部服务
make logs         # 查看所有服务日志
make logs-api     # 仅查看 API 服务日志
make build        # 重新构建镜像
make test         # 运行单元测试
make test-all     # 运行全部测试
make shell        # 进入 API 容器
make db-reset     # 重置数据库
make clean       # 清除所有 Docker 资源
```

## 🔄 扩展完善（5 项全部完成 ✅）

| 扩展 | 状态 | 实现方式 | 核心文件 |
|------|------|---------|---------|
| 高德地图 API 路线规划 | ✅ 已完成 | 高德地图 API + Haversine fallback | [amap_service.py](src/tools/amap_service.py) |
| 餐厅实时评价搜索 | ✅ 已完成 | 高德 POI 搜索 + Mock 数据降级 | [restaurants.py](src/tools/restaurants.py) |
| BGE Embedding 向量检索 | ✅ 已完成 | BGE-small-zh-v1.5 + BM25 融合 + TF-IDF 降级 | [embeddings.py](src/rag/embeddings.py), [retriever.py](src/rag/retriever.py) |
| Token 用量追踪 | ✅ 已完成 | tiktoken + 字符估算 + DeepSeek 定价模型 | [token_tracker.py](src/server/token_tracker.py) |
| 酒店预订工具 | ✅ 已完成 | 高德 POI 酒店搜索 + Mock 数据降级 | [hotels.py](src/tools/hotels.py) |

### 扩展后的 Agent 工具集（4 → 5 个工具）

| # | 工具 | 功能 | 数据来源 |
|---|------|------|---------|
| 1 | `search_attractions` | 搜索景点 | RAG / Mock |
| 2 | `get_weather` | 天气查询 | wttr.in API |
| 3 | `plan_route` | 路线规划 🆕 | 高德地图 API / Haversine |
| 4 | `search_restaurants` | 美食搜索 🆕 | 高德 POI / Mock |
| 5 | `search_hotels` | 🆕 酒店搜索 | 高德 POI / Mock |

### 扩展架构

```
Agent (5 Tools)
├── search_attractions → RAG (BM25 + BGE Embedding)
├── get_weather → wttr.in API
├── plan_route → AmapService (geocode + distance + transit)
├── search_restaurants → AmapService (POI search)
└── search_hotels → AmapService (POI search)

AmapService
├── 高德 API 可用 → 真实地理数据
├── API Key 缺失 → fallback 坐标库 + Haversine 公式
└── 网络异常 → fallback 坐标库 + Haversine 公式

HybridRetriever V2
├── BGE Embedding 可用 → BM25(0.3) + 向量相似度(0.7)
├── BGE 下载失败 → 纯 BM25 关键词匹配
└── 无外部库 → TF-IDF 字符级 n-gram

TokenTracker
├── tiktoken 可用 → 精确 token 计数
├── tiktoken 未安装 → 字符估算 (中文/1.5, 英文/4)
└── 成本模型 → DeepSeek 实时定价
```

> 📄 详细实施步骤见 [docs/EXTENSIONS_IMPLEMENTATION.md](docs/EXTENSIONS_IMPLEMENTATION.md)

---

*Day 1-10 逐步搭建，每一步都可追溯。*
