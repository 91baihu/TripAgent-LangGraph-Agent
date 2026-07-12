"""TripAgent FastAPI 入口 — 生产级 API 服务"""

import os
import time
import uuid
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from .routes import chat, trips, tools, auth, credits, sessions, export, billing, admin
from .logging import logger
from .middleware import DeviceFingerprintMiddleware


# ========== 应用生命周期 ==========
@asynccontextmanager
async def lifespan(app: FastAPI):
    """启动/关闭钩子"""
    logger.info(f"tripagent_starting env={os.getenv('APP_ENV', 'dev')}")

    # 初始化数据库表（先导入 models 确保所有表注册到 Base.metadata）
    try:
        from . import models  # noqa: F401  # 确保 ORM 模型已注册
        from .database import init_db
        await init_db()
        logger.info("database_initialized")
    except Exception as e:
        logger.error(f"database_init_failed error={e}")

    yield

    logger.info("tripagent_shutting_down")
    try:
        from .database import close_db
        await close_db()
    except ImportError:
        pass


def create_app() -> FastAPI:
    """创建 FastAPI 应用（工厂模式）"""
    app = FastAPI(
        title="TripAgent API",
        description="AI 旅行规划 Agent — LangGraph 多工具调用",
        version="1.0.0",
        docs_url="/api/docs",
        redoc_url="/api/redoc",
        lifespan=lifespan,
    )

    # CORS 中间件
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "http://localhost:5173",  # Vite dev
            "http://localhost:5174",  # Vite dev (fallback)
            "http://localhost:3000",  # React dev
            "http://localhost:80",  # Nginx
            "http://127.0.0.1:5173",
            "http://127.0.0.1:5174",
            "http://127.0.0.1:3000",
        ],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # 设备指纹中间件（解析 X-Device-Fingerprint header）
    app.add_middleware(DeviceFingerprintMiddleware)

    # 请求 ID + 访问日志中间件
    @app.middleware("http")
    async def request_middleware(request: Request, call_next):
        request_id = request.headers.get("X-Request-ID", str(uuid.uuid4())[:8])
        request.state.request_id = request_id
        start_time = time.time()

        response = await call_next(request)

        # 访问日志
        latency_ms = (time.time() - start_time) * 1000
        logger.info(
            f"request method={request.method} path={request.url.path} "
            f"status={response.status_code} latency={round(latency_ms, 1)}ms "
            f"rid={request_id}"
        )
        response.headers["X-Request-ID"] = request_id
        return response

    # 全局异常处理
    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        request_id = getattr(request.state, "request_id", "unknown")
        logger.error(
            f"unhandled_error path={request.url.path} "
            f"error={str(exc)} rid={request_id}"
        )
        return JSONResponse(
            status_code=500,
            content={
                "error": "internal_server_error",
                "message": "服务器内部错误，请稍后重试",
                "request_id": request_id,
            },
        )

    # 注册路由
    app.include_router(chat.router, prefix="/api/v1", tags=["对话"])
    app.include_router(trips.router, prefix="/api/v1", tags=["行程"])
    app.include_router(tools.router, prefix="/api/v1", tags=["工具"])
    app.include_router(auth.router, prefix="/api/v1", tags=["认证"])
    app.include_router(credits.router, prefix="/api/v1", tags=["额度"])
    app.include_router(sessions.router, prefix="/api/v1", tags=["会话"])
    app.include_router(export.router, prefix="/api/v1", tags=["导出"])
    app.include_router(billing.router, prefix="/api/v1", tags=["付费"])
    app.include_router(admin.router, prefix="/api/v1", tags=["管理员"])

    # 健康检查
    @app.get("/health")
    async def health():
        return {"status": "healthy", "version": "1.0.0", "env": os.getenv("APP_ENV", "dev")}

    return app


app = create_app()
