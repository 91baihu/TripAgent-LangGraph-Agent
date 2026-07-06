# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project overview

TripAgent is an AI-powered travel planning agent built on **LangGraph**. Users describe travel needs in natural language; the Agent autonomously invokes multiple tools (attraction search, weather, route planning, restaurant search), performs multi-step reasoning via a ReAct loop, and outputs a complete travel itinerary.

The project has **two entry points**: a **Streamlit** app (`src/main.py`) for quick prototyping with reasoning trace visualization, and a production **FastAPI** server (`src/server/main.py`) with JWT auth, SSE streaming, PostgreSQL persistence, and Redis caching — all orchestrated via Docker Compose. A **React + TypeScript + Tailwind** frontend lives in `frontend/` for the full web-client experience.

## Tech stack

| Layer | Technology |
|-------|-----------|
| Agent framework | LangGraph (`StateGraph`), LangChain tools (`@tool` decorator) |
| LLM | DeepSeek Chat API via `langchain-deepseek` |
| API server | FastAPI (async), SSE streaming via `sse-starlette` |
| Database | PostgreSQL 16 + SQLAlchemy 2.0 async (`asyncpg`) |
| Cache | Redis 7 (with in-memory dict fallback for dev) |
| Auth | JWT (python-jose) + bcrypt password hashing |
| Prototyping UI | Streamlit (chat + reasoning trace sidebar) |
| Web frontend | React 18 + TypeScript + Vite + Tailwind CSS |
| RAG | Custom `HybridRetriever` (keyword TF scoring, designed for future BM25 + embedding upgrade) |
| Lint/format | Ruff |
| Testing | pytest + pytest-asyncio |
| Infrastructure | Docker Compose (api, postgres, redis, nginx, admin) |

## Commands

### Local development (bare metal)

```bash
# Install dependencies
pip install -r requirements.txt

# Run the Streamlit prototyping app (requires DEEPSEEK_API_KEY in .env)
cd src && streamlit run main.py

# Run the FastAPI server directly
cd src && uvicorn server.main:app --reload --port 8000

# Run unit tests only (no API key needed)
pytest tests/ -v -k "not AgentIntegration"

# Run all tests (requires DEEPSEEK_API_KEY set)
pytest tests/ -v

# Lint & format check
ruff check src/ tests/
ruff format --check src/ tests/
```

### Docker development (recommended)

```bash
# Start core services (api + postgres + redis)
make up

# Start full dev environment (includes Streamlit admin panel on :8501)
make up-dev

# Stop everything
make down

# Run tests inside container
make test

# View API logs
make logs-api

# Reset database
make db-reset

# Rebuild images after dependency changes
make build
```

### Frontend

```bash
cd frontend
npm install
npm run dev      # Vite dev server on :5173
npm run build    # Production build
```

## Architecture

### Dual-entry design

```
                    ┌─────────────────────┐
                    │   LangGraph Agent   │
                    │   (src/agent/)      │
                    │   4 tools + ReAct   │
                    └────────┬────────────┘
                             │
              ┌──────────────┴──────────────┐
              │                             │
    ┌─────────┴─────────┐       ┌──────────┴──────────┐
    │  Streamlit app     │       │  FastAPI server      │
    │  src/main.py       │       │  src/server/main.py  │
    │  (prototyping UI)  │       │  (production API)    │
    └───────────────────┘       └──────────┬───────────┘
                                           │
                        ┌──────────────────┼──────────────────┐
                        │                  │                  │
                  ┌──────┴──────┐   ┌──────┴──────┐   ┌──────┴──────┐
                  │ PostgreSQL  │   │   Redis     │   │   React     │
                  │ (trips,     │   │ (cache,     │   │   frontend  │
                  │  users,     │   │  sessions,  │   │   :5173     │
                  │  audit log) │   │  rate limit)│   │             │
                  └─────────────┘   └─────────────┘   └─────────────┘
```

### Agent ReAct loop

```
User input → [agent node: LLM decides] → conditional edge → [tools node: execute] → back to agent → ... → END
```

See [src/agent/graph.py](src/agent/graph.py) — the `create_agent()` factory builds the `StateGraph`, binds 4 tools to the LLM, and wires the agent/tools nodes with the `should_continue` conditional edge. The agent catches LLM API failures and returns a user-friendly error instead of crashing.

### FastAPI server structure (`src/server/`)

| File | Role |
|------|------|
| [main.py](src/server/main.py) | App factory (`create_app()`), CORS, request-id middleware, global exception handler, route registration |
| [services/agent_service.py](src/server/services/agent_service.py) | `TravelAgentService` — wraps the LangGraph agent for SSE streaming (`stream_chat`) and sync (`chat_sync`); lazy-inits the agent |
| [routes/chat.py](src/server/routes/chat.py) | `POST /api/v1/chat/stream` (SSE), `POST /api/v1/chat` (sync); degrades to sync if `sse-starlette` unavailable |
| [routes/trips.py](src/server/routes/trips.py) | Full CRUD for trips + share-token generation; currently in-memory storage, designed for PostgreSQL migration |
| [routes/auth.py](src/server/routes/auth.py) | Register, login, refresh-token, `/me`; in-memory user store |
| [routes/tools.py](src/server/routes/tools.py) | Debug endpoints to test each tool individually + `GET /api/v1/tools` tool catalog |
| [auth.py](src/server/auth.py) | JWT creation/verification, bcrypt password hashing (with passlib fallback), `get_current_user`/`require_role` FastAPI dependencies, API key generation |
| [models.py](src/server/models.py) | SQLAlchemy ORM: `User`, `Trip`, `ToolCallLog`, `ApiKey`, `UserPreference` with indexes and relationships |
| [database.py](src/server/database.py) | Async SQLAlchemy engine + session factory, `get_db` dependency, `init_db`/`close_db` lifecycle |
| [cache.py](src/server/cache.py) | `CacheService` — Redis caching with in-memory dict fallback; caches tool results (5min TTL), sessions (30min), and rate-limit counters |
| [middleware.py](src/server/middleware.py) | `CircuitBreaker` (LLM API protection, 5-failure threshold), `TokenBucketRateLimiter` (per-user/IP rate limiting), `RequestIDMiddleware` |
| [logging.py](src/server/logging.py) | Structured logging via structlog (JSON format in prod, standard logging fallback); `LogContext` defines canonical field names for tracing |
| [schemas/](src/server/schemas/) | Pydantic models for chat requests/responses and trip CRUD |

### Agent core (`src/agent/`)

| File | Role |
|------|------|
| [graph.py](src/agent/graph.py) | `create_agent()` factory — binds 4 tools to `ChatDeepSeek`, defines `agent_node` (injects system prompt on first call), `should_continue` router, and `tool_node`; returns compiled `StateGraph` |
| [state.py](src/agent/state.py) | `AgentState` TypedDict: `messages` (auto-append via `add_messages` reducer), `next_step`, `travel_plan` |
| [prompts.py](src/agent/prompts.py) | Layered system prompt: role → workflow → output format constraints → rules |

### Tools (`src/tools/`)

Each tool uses `@tool` decorator with Google-style docstrings — LangChain auto-generates the function schema for the LLM from the decorator and docstring. All tools are mock-data-backed except weather (which calls wttr.in).

### Docker Compose services

| Service | Image | Role |
|---------|-------|------|
| `postgres` | postgres:16-alpine | User, trip, and audit-log data |
| `redis` | redis:7-alpine | Tool cache, sessions, rate limiting |
| `api` | Dockerfile (python:3.12-slim) | FastAPI on `:8000`, auto-falls back to Streamlit if server code missing |
| `admin` | Dockerfile | Streamlit prototyping UI on `:8501` (profile: `dev`) |
| `nginx` | nginx:1.27-alpine | Reverse proxy on `:80` (profile: `prod`) |

The Dockerfile is a multi-stage build (builder → runtime) running as non-root `tripagent` user with a health check on `/health`.

### CI/CD (GitHub Actions)

- **CI** ([.github/workflows/ci.yml](.github/workflows/ci.yml)): Triggered on PRs to `main`/`develop` and pushes to `develop`. Jobs: ruff lint/format → unit tests (Python 3.11 + 3.12 matrix, no API key needed) → integration tests (PR only, uses `DEEPSEEK_API_KEY` secret) → Docker build verification.
- **CD** ([.github/workflows/cd.yml](.github/workflows/cd.yml)): Triggered on push to `main` (staging deploy) and version tags `v*` (production deploy). Builds & pushes Docker image to GHCR, then SSH-deploys to staging/production with health checks.

### React frontend (`frontend/`)

React 18 + TypeScript + Vite + Tailwind CSS. Feature-based structure: `features/auth/`, `features/chat/`, `features/trips/`, `features/map/`. Shared component library in `src/components/` (Button, Card, Modal, Toast, Bubble, etc.). State management via Zustand stores (`authStore`, `chatStore`). SSE chat streaming via custom `useChatStream` hook against the FastAPI `/api/v1/chat/stream` endpoint.

### Environment configuration

Copy `config/.env.example` to `config/dev.env` or `config/prod.env`. Key variables: `DEEPSEEK_API_KEY`, `POSTGRES_*`, `JWT_SECRET_KEY`, `REDIS_URL`. Third-party API keys (Amap, HeFeng, Ctrip) are optional future integrations. Rate limiting and token budget are configurable per environment.
