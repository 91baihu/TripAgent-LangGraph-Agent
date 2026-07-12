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
- **用户体系**：JWT 注册/登录、游客设备指纹、新用户 10 次试用额度、游客 1 次免费体验
- **商业化系统**：4 档套餐（免费/Pro 月付/Pro 年付/家庭）、额度流水、购买订单
- **会话持久化**：聊天历史自动保存、游客会话 → 登录用户迁移
- **行程导出**：支持 Markdown / HTML / PDF / DOCX / 纯文本 5 种格式一键导出
- **双数据库支持**：PostgreSQL 16（生产）+ SQLite（开发兜底），`USE_SQLITE=1` 一键切换
- **熔断 & 限流**：LLM API 熔断器 + Token Bucket 限流器
- **Docker 一键部署**：PostgreSQL + Redis + Nginx 反向代理
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
    ┌────────────────────────────────────────────┼────────────────────────────────────┐
    │               │                │           │            │               │        │
    │          ┌────┴────┐   ┌──────┴──────┐ ┌──┴──┐  ┌─────┴─────┐ ┌──────┴──────┐ │
    │          │PostgreSQL│   │   Redis     │ │SQLite│  │  Services │ │ React 前端  │ │
    │          │(生产)    │   │ 缓存/限流   │ │(开发)│  │           │ │ Vite :5173  │ │
    │          │          │   │ 会话管理    │ │      │  │           │ │             │ │
    │          └──────────┘   └─────────────┘ └──────┘ └─────┬─────┘ └─────────────┘ │
    │                                                        │                       │
    │    ┌───────────────────────────────────────────────────┴──────────────────┐    │
    │    │  CreditService │ SessionService │ ExportService │ BillingService     │    │
    │    │  额度/套餐管理  │ 会话/消息持久化 │ 5格式行程导出  │ 订单/支付模拟      │    │
    │    └──────────────────────────────────────────────────────────────────────┘    │
    └────────────────────────────────────────────────────────────────────────────────┘
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

# === SQLite 模式（无需 PostgreSQL/Redis，推荐开发使用）===
cd src && USE_SQLITE=1 uvicorn server.main:app --reload --port 8001

# === 完整模式（需先启动 PostgreSQL + Redis）===
cd src && uvicorn server.main:app --reload --port 8000

# Streamlit 原型
cd src && streamlit run main.py
```

### React 前端

```bash
cd frontend
npm install
npm run dev     # http://localhost:5173（API 代理到 :8001）
```

> **开发模式**：`USE_SQLITE=1` 使用 SQLite 数据库，无需 Docker。前端代理端口见 `frontend/vite.config.ts`。

## 🧪 测试

```bash
pytest tests/ -v -k "not AgentIntegration"   # 不需 API Key
pytest tests/ -v                              # 全部测试（需 DEEPSEEK_API_KEY）
make test                                     # Docker 中运行
```

## 👤 用户体系 & 商业化

| 角色 | 免费额度 | 限制说明 |
|------|---------|---------|
| **游客**（设备指纹） | 1 次 | 用完需注册登录 |
| **注册用户**（免费版） | 10 次试用 | 额度用完可继续对话，保存/导出受限 |
| **Pro 月付** | 100 次/月 | ¥29/月 |
| **Pro 年付** | 1200 次/年 | ¥199/年 |
| **家庭版** | 300 次/月 | ¥59/月，支持 5 人共享 |

- **设备指纹**：基于 @fingerprintjs/fingerprintjs，游客无需注册即可体验
- **会话迁移**：游客登录后自动将设备会话迁移至用户账户
- **额度流水**：每次消费/获取额度均有 `credit_transactions` 记录
- **订单系统**：`purchase_orders` 表记录套餐购买，支持支付模拟

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
│   │   ├── attractions.py      # 景点搜索 (RAG)
│   │   ├── weather.py          # 天气查询
│   │   ├── route.py            # 路线规划（高德 / Haversine）
│   │   ├── restaurants.py      # 美食搜索（高德 POI）
│   │   ├── hotels.py           # 酒店搜索（高德 POI）
│   │   ├── amap_service.py     # 高德地图 API 封装
│   │   └── result_parser.py    # 工具结果解析
│   ├── server/                 # FastAPI 生产级后端
│   │   ├── main.py             # 应用入口（工厂模式，8 个路由模块）
│   │   ├── auth.py             # JWT + bcrypt 认证
│   │   ├── models.py           # SQLAlchemy ORM（11 张表，双数据库兼容）
│   │   ├── database.py         # 异步数据库引擎（PostgreSQL/SQLite 自适应）
│   │   ├── cache.py            # Redis 缓存（含内存 dict 降级）
│   │   ├── middleware.py       # 设备指纹 · 熔断器 · 限流器 · 请求ID · 访问日志
│   │   ├── logging.py          # 结构化日志（structlog）
│   │   ├── routes/             # 8 个路由模块
│   │   │   ├── chat.py         # SSE 流式对话 + 同步对话
│   │   │   ├── trips.py        # 行程 CRUD + 分享
│   │   │   ├── auth.py         # 注册/登录/刷新令牌/当前用户
│   │   │   ├── tools.py        # 工具目录 + 单独测试
│   │   │   ├── credits.py      # 额度查询
│   │   │   ├── sessions.py     # 会话列表/详情/消息/归档
│   │   │   ├── export.py       # 行程导出（md/html/pdf/docx/txt）
│   │   │   └── billing.py      # 套餐列表/下单/支付/管理
│   │   ├── schemas/            # Pydantic 请求/响应模型
│   │   └── services/           # 业务服务层
│   │       ├── agent_service.py    # Agent SSE 流式 + 同步封装
│   │       ├── credit_service.py   # 额度检查/消费/套餐/试用赠送
│   │       ├── session_service.py  # 会话创建/消息持久化/游客迁移
│   │       ├── export_service.py   # 5 格式行程导出
│   │       └── billing_service.py  # 订单创建/支付确认/额度授予
│   └── rag/
│       ├── retriever.py        # HybridRetriever (BM25 + BGE)
│       ├── embeddings.py       # BGE Embedding
│       └── data/               # 景区知识库
├── frontend/                   # React 前端
│   ├── vite.config.ts          # Vite 配置（含 API 代理）
│   └── src/
│       ├── components/         # 通用组件
│       │   ├── Button/Card/Modal/Toast/...  # 基础 UI 组件
│       │   ├── Timeline/                   # 行程时间线
│       │   ├── WeatherCard/                # 天气卡片
│       │   ├── Skeleton/                   # 骨架屏
│       │   ├── ErrorBoundary/              # 错误边界
│       │   ├── QuotaBar/                   # 额度进度条
│       │   └── ExportMenu/                 # 导出菜单（5 格式）
│       ├── features/           # 功能页面
│       │   ├── auth/           # 登录/注册
│       │   ├── chat/           # 对话页（含地图/可视化面板）
│       │   ├── trips/          # 行程列表/详情/导出
│       │   ├── map/            # 地图视图
│       │   └── billing/        # 套餐定价页
│       ├── hooks/              # useChatStream / useDeviceFingerprint
│       ├── stores/             # Zustand（authStore / chatStore / quotaStore）
│       └── services/           # API 客户端（含设备指纹自动注入）
├── docs/                       # 详细文档
└── tests/
```

## 🛠️ 技术栈

| 组件 | 技术 |
|------|------|
| Agent 框架 | LangGraph + LangChain |
| LLM | DeepSeek Chat API |
| API 服务 | FastAPI (async) + SSE |
| 数据库 | PostgreSQL 16（生产） / SQLite（开发），SQLAlchemy 2.0 async |
| 缓存 | Redis 7（含内存 dict 降级） |
| 认证 | JWT (python-jose) + bcrypt |
| 设备指纹 | @fingerprintjs/fingerprintjs |
| 原型 UI | Streamlit |
| Web 前端 | React 18 + TypeScript + Vite + Tailwind CSS |
| 状态管理 | Zustand |
| RAG | HybridRetriever (BGE Embedding + BM25) |
| 文档导出 | markdown + python-docx（MD/HTML/PDF/DOCX/TXT） |
| 地图服务 | 高德地图 API |
| 部署 | Docker Compose + Nginx |
| CI/CD | GitHub Actions |
| 测试 | pytest + pytest-asyncio |
| 代码质量 | Ruff |

## 📡 API 接口

### 对话
| 方法 | 路径 | 说明 |
|------|------|------|
| `POST` | `/api/v1/chat/stream` | SSE 流式对话（含额度检查 & 消息持久化） |
| `POST` | `/api/v1/chat` | 同步对话 |

### 认证
| 方法 | 路径 | 说明 |
|------|------|------|
| `POST` | `/api/v1/auth/register` | 注册（自动赠送 10 次试用额度） |
| `POST` | `/api/v1/auth/login` | 登录（自动迁移游客会话） |
| `POST` | `/api/v1/auth/refresh` | 刷新令牌 |
| `GET` | `/api/v1/auth/me` | 当前用户信息 |

### 行程
| 方法 | 路径 | 说明 |
|------|------|------|
| `POST` | `/api/v1/trips` | 创建行程 |
| `GET` | `/api/v1/trips` | 行程列表 |
| `GET` | `/api/v1/trips/{id}` | 行程详情 |
| `PATCH` | `/api/v1/trips/{id}` | 更新行程 |
| `DELETE` | `/api/v1/trips/{id}` | 删除行程 |
| `POST` | `/api/v1/trips/{id}/share` | 生成分享链接 |

### 额度 & 套餐
| 方法 | 路径 | 说明 |
|------|------|------|
| `GET` | `/api/v1/credits/status` | 查询额度状态（游客/登录用户） |
| `GET` | `/api/v1/plans` | 套餐列表（4 档） |

### 会话
| 方法 | 路径 | 说明 |
|------|------|------|
| `GET` | `/api/v1/sessions` | 会话列表（分页） |
| `GET` | `/api/v1/sessions/{id}` | 会话详情 |
| `GET` | `/api/v1/sessions/{id}/messages` | 会话消息列表 |
| `PATCH` | `/api/v1/sessions/{id}` | 更新会话（归档/重命名） |
| `DELETE` | `/api/v1/sessions/{id}` | 删除会话 |

### 导出
| 方法 | 路径 | 说明 |
|------|------|------|
| `GET` | `/api/v1/trips/{id}/export?format=md` | 下载行程文件（md/html/pdf/docx） |
| `GET` | `/api/v1/trips/{id}/export/text` | 获取纯文本（一键复制） |
| `GET` | `/api/v1/trips/{id}/export/preview?format=html` | 导出预览 |

### 订单（需登录）
| 方法 | 路径 | 说明 |
|------|------|------|
| `GET` | `/api/v1/billing/plans` | 套餐列表 |
| `POST` | `/api/v1/billing/orders` | 创建订单 |
| `GET` | `/api/v1/billing/orders` | 我的订单 |
| `GET` | `/api/v1/billing/orders/{id}` | 订单详情 |
| `POST` | `/api/v1/billing/orders/{id}/cancel` | 取消订单 |
| `POST` | `/api/v1/billing/orders/{id}/pay` | 模拟支付 |

### 工具 & 系统
| 方法 | 路径 | 说明 |
|------|------|------|
| `GET` | `/api/v1/tools` | 工具目录 |
| `POST` | `/api/v1/tools/{name}` | 单独测试工具 |
| `GET` | `/health` | 健康检查 |

> 启动后访问 `http://localhost:8001/api/docs`（或 `:8000`）查看 Swagger 文档。共 **34 个 API 端点**。

## 📝 Makefile

```bash
make up           # 启动核心服务（api + postgres + redis）
make up-dev       # 启动开发环境（含 Streamlit :8501）
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
| [01-项目概述与技术演进](docs/01-项目概述与技术演进.md) | 项目概述、架构总览、演进历程 |
| [02-扩展功能实施记录](docs/02-扩展功能实施记录.md) | 高德/BGE/Token/酒店等扩展细节 |
| [03-产品化架构方案](docs/03-产品化架构方案.md) | 部署架构、安全体系、商业模式 |
| [04-前端设计系统方案](docs/04-前端设计系统方案.md) | Warm Editorial 设计系统、组件规格 |
| [05-天气API升级方案](docs/05-天气API升级方案.md) | 和风+彩云双API（远期规划） |
| [06-用户体系与商业化方案](docs/06-用户体系与商业化方案.md) | 用户体系、额度、导出、付费方案 |

## 📄 License

MIT
