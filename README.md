# ✈️ TripAgent — AI 旅行规划 Agent

基于 **LangGraph** 的多工具调用旅行规划 Agent。用户用自然语言描述需求，Agent 自主调用景点搜索、天气查询、路线规划、美食推荐、酒店搜索等工具，多步推理后输出完整旅行方案。

## 🎯 核心特性

- **LangGraph StateGraph** 驱动的 ReAct 循环
- **5 个 LangChain Tool**：景点搜索 · 天气查询 · 路线规划 · 美食推荐 · 酒店搜索
- **高德地图 API** 集成：真实地理编码、路线规划、POI 搜索
- **RAG 混合检索**：BGE Embedding + BM25 融合检索景点知识库
- **双入口架构**：Streamlit 快速原型 + FastAPI 生产级 API
- **SSE 流式对话**：服务端推送 Agent 每一步推理过程
- **React 前端**：TypeScript + Vite + Tailwind CSS，含地图、时间线、天气卡片等可视化组件
- **Docker 一键部署**：PostgreSQL + Redis + Nginx 反向代理
- **JWT 认证**：注册/登录/刷新令牌
- **CI/CD**：GitHub Actions 自动测试 → 构建镜像 → 部署

## 🏗️ 架构

```
                          ┌─────────────────────┐
                          │   LangGraph Agent   │
                          │   (src/agent/)      │
                          │   ReAct 循环        │
                          │   5 Tools           │
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

## 🔧 Agent 工具集

| 工具 | 功能 | 数据来源 |
|------|------|---------|
| `search_attractions` | 搜索景点 | RAG 混合检索 (BGE + BM25) |
| `get_weather` | 查询天气 | [wttr.in](https://wttr.in) API |
| `plan_route` | 路线规划 | 高德地图 API / Haversine 降级 |
| `search_restaurants` | 美食搜索 | 高德 POI 搜索 |
| `search_hotels` | 酒店搜索 | 高德 POI 搜索 |

## 🚀 快速开始

### Docker 部署（推荐）

```bash
git clone <your-repo-url> && cd trip-agent
cp config/.env.example config/dev.env
# 编辑 config/dev.env，填入 DEEPSEEK_API_KEY

make up-dev
# API 文档:    http://localhost:8000/api/docs
# Streamlit:  http://localhost:8501
```

### 本地开发

```bash
pip install -r requirements.txt
cp config/.env.example .env
# 编辑 .env，填入 DEEPSEEK_API_KEY=sk-your-key-here

# Streamlit 原型
cd src && streamlit run main.py

# 或 FastAPI 服务器
cd src && uvicorn server.main:app --reload --port 8000
```

### React 前端

```bash
cd frontend
npm install
npm run dev     # http://localhost:5173
```

## 🧪 测试

```bash
pytest tests/ -v -k "not AgentIntegration"   # 不需 API Key
pytest tests/ -v                              # 全部测试（需 DEEPSEEK_API_KEY）
make test                                     # Docker 中运行
```

## 📁 项目结构

```
trip-agent/
├── requirements.txt
├── Makefile / Dockerfile / docker-compose.yml
├── docker/
│   ├── init-db.sql
│   └── nginx.conf
├── config/
│   ├── .env.example
│   ├── dev.env
│   └── prod.env
├── .github/workflows/
│   ├── ci.yml                  # PR: lint + test + build
│   └── cd.yml                  # Push: build → deploy
├── src/
│   ├── main.py                 # Streamlit 入口
│   ├── agent/
│   │   ├── graph.py            # LangGraph 核心：StateGraph + ReAct
│   │   ├── state.py            # Agent 状态定义
│   │   └── prompts.py          # System Prompt
│   ├── tools/
│   │   ├── attractions.py      # 景点搜索
│   │   ├── weather.py          # 天气查询
│   │   ├── route.py            # 路线规划
│   │   ├── restaurants.py      # 美食搜索
│   │   ├── hotels.py           # 酒店搜索
│   │   ├── amap_service.py     # 高德地图 API 封装
│   │   └── result_parser.py    # 工具结果解析
│   ├── server/                 # FastAPI 生产级后端
│   │   ├── main.py             # 应用入口（工厂模式）
│   │   ├── auth.py             # JWT + bcrypt
│   │   ├── models.py           # SQLAlchemy ORM
│   │   ├── database.py         # 异步数据库引擎
│   │   ├── cache.py            # Redis 缓存（含内存降级）
│   │   ├── middleware.py       # 熔断器 + 限流器 + 请求ID
│   │   ├── logging.py          # 结构化日志
│   │   ├── routes/             # chat / trips / auth / tools
│   │   ├── schemas/            # Pydantic 请求/响应模型
│   │   └── services/           # Agent 服务封装（SSE + 同步）
│   └── rag/
│       ├── retriever.py        # HybridRetriever (BM25 + BGE)
│       ├── embeddings.py       # BGE Embedding
│       └── data/               # 景区知识库
├── frontend/                   # React 前端
│   ├── vite.config.ts
│   └── src/
│       ├── components/         # 通用组件（Button/Card/Modal/Toast/Timeline/WeatherCard...）
│       ├── features/           # auth / chat / trips / map
│       ├── hooks/              # useChatStream 等
│       ├── stores/             # Zustand 状态管理
│       └── services/           # API 客户端
├── docs/                       # 详细文档
└── tests/
```

## 🛠️ 技术栈

| 组件 | 技术 |
|------|------|
| Agent 框架 | LangGraph + LangChain |
| LLM | DeepSeek Chat API |
| API 服务 | FastAPI (async) + SSE |
| 数据库 | PostgreSQL 16 + SQLAlchemy 2.0 (async) |
| 缓存 | Redis 7（含内存降级） |
| 认证 | JWT (python-jose) + bcrypt |
| 原型 UI | Streamlit |
| Web 前端 | React 18 + TypeScript + Vite + Tailwind CSS |
| RAG | HybridRetriever (BGE Embedding + BM25) |
| 地图服务 | 高德地图 API |
| 部署 | Docker Compose + Nginx |
| CI/CD | GitHub Actions |
| 测试 | pytest + pytest-asyncio |
| 代码质量 | Ruff |

## 📡 API 接口

| 方法 | 路径 | 说明 |
|------|------|------|
| `POST` | `/api/v1/chat/stream` | SSE 流式对话 |
| `POST` | `/api/v1/chat` | 同步对话 |
| `POST` | `/api/v1/auth/register` | 注册 |
| `POST` | `/api/v1/auth/login` | 登录 |
| `POST` | `/api/v1/auth/refresh` | 刷新令牌 |
| `GET` | `/api/v1/auth/me` | 当前用户 |
| `POST` | `/api/v1/trips` | 创建行程 |
| `GET` | `/api/v1/trips` | 行程列表 |
| `GET` | `/api/v1/trips/{id}` | 行程详情 |
| `PATCH` | `/api/v1/trips/{id}` | 更新行程 |
| `DELETE` | `/api/v1/trips/{id}` | 删除行程 |
| `POST` | `/api/v1/trips/{id}/share` | 分享行程 |
| `GET` | `/api/v1/tools` | 工具列表 |
| `POST` | `/api/v1/tools/{name}` | 测试工具 |
| `GET` | `/health` | 健康检查 |

> 启动后访问 `http://localhost:8000/api/docs` 查看 Swagger 文档。

## 📝 Makefile

```bash
make up           # 启动核心服务
make up-dev       # 启动开发环境（含 Streamlit）
make down         # 停止全部服务
make logs-api     # 查看 API 日志
make build        # 重新构建镜像
make test         # 运行测试
make db-reset     # 重置数据库
make clean        # 清除 Docker 资源
```

## 📚 文档

详细文档见 [`docs/`](docs/) 目录：

| 文档 | 说明 |
|------|------|
| [docs/README.md](docs/README.md) | 文档索引 |
| [01-项目初始方案](docs/01-项目初始方案-10天搭建指南.md) | 搭建教程 |
| [02-完成总结](docs/02-初始阶段完成总结.md) | 初始阶段总结 |
| [03-扩展实施记录](docs/03-扩展实施记录-5项扩展.md) | 高德/BGE/Token/酒店等扩展 |
| [04-企业级产品化方案](docs/04-企业级产品化方案-从Demo到产品.md) | 部署/商业模式 |
| [05-可视化优化方案](docs/05-可视化优化方案-地图排行榜时间线.md) | 地图/排行榜/时间线 |
| [06-全链路追踪与扩展集成](docs/06-全链路追踪与扩展集成-实施步骤.md) | UI 优化 + 全链路验证 |
