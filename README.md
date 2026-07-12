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

### 0. 前置条件

| 软件 | 最低版本 | 用途 | 必须 |
|------|---------|------|------|
| Python | 3.11+ | 后端运行环境 | ✅ |
| Node.js | 18+ | 前端构建 | ✅（本地跑前端时需要） |
| Git | 任意 | 克隆代码 | ✅ |
| Docker Desktop | 24+ | 容器化部署 | ⬜（方式一/二需要） |
| DeepSeek API Key | — | LLM 调用 | ✅ [获取地址](https://platform.deepseek.com) |

---

### 方式一：Docker 全部托管（最简单，3 步启动）

> 适用：不想手动装 Python/Node、需要完整 PostgreSQL+Redis+Nginx 环境。

#### 步骤 1：安装 Docker Desktop

前往 [docker.com](https://www.docker.com/products/docker-desktop) 下载安装。

- **Windows**：安装后确保 WSL2 已启用，Docker Desktop 右下角图标变绿即为就绪。
- **macOS**：拖入 Applications，Docker Desktop 菜单栏图标变绿即为就绪。
- **Linux**：`curl -fsSL https://get.docker.com | sh && sudo systemctl enable --now docker`

验证安装：

```bash
docker --version
docker ps          # 不报错即可
```

#### 步骤 2：配置环境变量

```bash
git clone <your-repo-url> && cd trip-agent

# 复制并编辑配置
cp config/.env.example config/dev.env
```

编辑 `config/dev.env`，**只需填一行**，其他保持默认：

```ini
DEEPSEEK_API_KEY=sk-你的真实Key
```

#### 步骤 3：启动服务

```bash
# 开发环境（API + PostgreSQL + Redis + Streamlit 管理面板）
make up-dev

# 或者只启动核心服务（API + PostgreSQL + Redis）
make up

# 生产环境（含 Nginx 反向代理）
make up-prod
```

**启动后的访问地址：**

| 服务 | 地址 |
|------|------|
| API 文档 (Swagger) | http://localhost:8000/api/docs |
| Streamlit 原型 UI | http://localhost:8501（仅 `make up-dev`） |
| React 前端 | 需单独 `cd frontend && npm run dev`，或 Nginx 静态托管 |
| PostgreSQL | `localhost:5432`，用户 `tripagent` |
| Redis | `localhost:6379` |

> Docker 镜像首次拉取需要几分钟（约 300MB），后续启动秒级完成。

---

### 方式二：混合模式 — Docker 数据库 + 本地跑后端（推荐开发）

> 适用：想用 PostgreSQL/Redis 但需要频繁改代码 & 热重载。

#### 步骤 1：安装 Docker Desktop 并启动数据库

```bash
# 配置 .env（项目根目录）
cp config/.env.example .env
# 编辑 .env，填入 DEEPSEEK_API_KEY
```

`.env` 关键配置（本地连 Docker 数据库时 `POSTGRES_HOST=localhost`）：

```ini
DEEPSEEK_API_KEY=sk-你的真实Key
POSTGRES_USER=tripagent
POSTGRES_PASSWORD=tripagent_dev
POSTGRES_DB=tripagent
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
REDIS_URL=redis://localhost:6379/0
```

```bash
# 只启动数据库和缓存
docker-compose --env-file .env up -d postgres redis
```

验证数据库就绪：

```bash
docker ps
# tripagent-db     ... Up ... (healthy)
# tripagent-redis  ... Up ... (healthy)
```

#### 步骤 2：启动后端

```bash
# 创建虚拟环境
python -m venv .venv && .venv\Scripts\activate   # Windows
python -m venv .venv && source .venv/bin/activate # macOS/Linux

# 安装 Python 依赖
pip install -r requirements.txt

# 启动 FastAPI（热重载模式）
cd src
uvicorn server.main:app --reload --port 8000
```

#### 步骤 3：启动前端

另开一个终端：

```bash
cd frontend
npm install
npm run dev        # http://localhost:5173
```

> ⚠️ 前端 Vite 代理端口需和后台一致。后端跑 `8000` → `vite.config.ts` 的 `target` 写 `http://localhost:8000`。

---

### 方式三：纯本地 SQLite 模式（零依赖，最快上手）

> 适用：只想快速体验、不装 Docker、不需要数据库和缓存。

```bash
# 1. 配置
cp config/.env.example .env
# 编辑 .env，填入 DEEPSEEK_API_KEY=sk-你的真实Key

# 2. 安装依赖
python -m venv .venv && .venv\Scripts\activate  # Windows
pip install -r requirements.txt aiosqlite

# 3. 启动后端（SQLite 模式）
cd src

# Windows PowerShell:
$env:USE_SQLITE="1"; uvicorn server.main:app --reload --port 8001

# macOS / Linux / Git Bash:
USE_SQLITE=1 uvicorn server.main:app --reload --port 8001

# 4. 另开终端启动前端
cd frontend
npm install && npm run dev
```

SQLite 数据库文件 `tripagent_dev.db` 会自动创建在项目根目录。

---

### 方式四：Streamlit 原型（单文件，无需前后端分离）

```bash
pip install -r requirements.txt
cd src
streamlit run main.py  # http://localhost:8501
```

> 此方式仅体验 Agent 推理流程，不含用户体系、商业化、导出等完整功能。

---

### 三种模式对比

| 维度 | 方式一 Docker 全托管 | 方式二 混合模式 | 方式三 SQLite |
|------|-------------------|---------------|-------------|
| 需要安装 | Docker | Docker + Python + Node | Python + Node |
| 数据库 | PostgreSQL | PostgreSQL | SQLite（单文件） |
| 缓存 | Redis | Redis | 内存 dict 降级 |
| 热重载 | ✅ Docker volume | ✅ uvicorn --reload | ✅ uvicorn --reload |
| 生产一致性 | ⭐⭐⭐ 完全一致 | ⭐⭐ 数据库一致 | ⭐ 仅逻辑一致 |
| 启动时间 | 3-5 分钟（首次） | 1-2 分钟 | 10 秒 |
| 推荐场景 | 验证部署、演示 | 日常开发 | 快速体验、前端调试 |

---

### 🐳 Docker 常用命令速查

```bash
# ===== 启动 / 停止 =====
make up              # 启动核心服务（api + db + redis）
make up-dev          # 启动开发环境（含 Streamlit :8501）
make up-prod         # 启动生产环境（含 Nginx :80）
make down            # 停止全部服务
make down-clean      # 停止服务并清除数据卷

# ===== 日志 =====
make logs            # 所有服务日志
make logs-api        # 仅 API 日志
docker logs tripagent-db    # 仅看数据库日志

# ===== 构建 & 调试 =====
make build           # 重新构建镜像（依赖变更后）
make test            # 在容器中运行单元测试
make shell           # 进入 API 容器 bash
make db-reset        # 清空数据库重新初始化

# ===== 数据库直连 =====
docker exec -it tripagent-db psql -U tripagent -d tripagent
# 常用 SQL：
#   \dt              — 列出全部表
#   SELECT * FROM users;
#   \q               — 退出

# ===== 清理 =====
make clean           # 删除所有容器、镜像、数据卷
docker system prune -a  # 清理 Docker 全局缓存
```

### 🛠️ 常见问题排查

| 问题 | 原因 | 解决 |
|------|------|------|
| `port 8000 already in use` | 端口被占用 | 改端口 `--port 8002`，同步改 `vite.config.ts` proxy |
| `database_init_failed` | PostgreSQL 未就绪 | `docker ps` 确认容器 healthy，等 10 秒重试 |
| `could not translate host name "postgres"` | 本地跑后端但用了 Docker 主机名 | `.env` 中 `POSTGRES_HOST=localhost` |
| 前端页面空白 / API 404 | 代理端口不匹配 | 检查 `vite.config.ts` target 端口与后台一致 |
| Docker 启动慢/卡住 | 国内网络拉镜像慢 | 配置 Docker 镜像加速器（阿里云/中科大） |
| `ModuleNotFoundError: asyncpg` | 缺 PostgreSQL 驱动 | `pip install asyncpg`（PostgreSQL 模式需要） |

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
