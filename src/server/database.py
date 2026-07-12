"""数据库配置 — SQLAlchemy async engine + session factory

支持 PostgreSQL（生产）和 SQLite（开发兜底）。
通过 USE_SQLITE=1 环境变量切换。
"""

import os
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase


# ========== 数据库 URL 构建 ==========
def get_database_url() -> str:
    """从环境变量构建异步数据库 URL

    优先级: DATABASE_URL > POSTGRES_URL > 独立 POSTGRES_* 变量 > SQLite 兜底
    """
    use_sqlite = os.getenv("USE_SQLITE", "").lower() in ("1", "true", "yes")

    database_url = os.getenv("DATABASE_URL") or os.getenv("POSTGRES_URL")
    if database_url and not use_sqlite:
        if "asyncpg" not in database_url and "sqlite" not in database_url:
            database_url = database_url.replace("postgresql://", "postgresql+asyncpg://")
            database_url = database_url.replace("postgres://", "postgresql+asyncpg://")
        return database_url

    if not use_sqlite:
        user = os.getenv("POSTGRES_USER", "tripagent")
        password = os.getenv("POSTGRES_PASSWORD", "tripagent_dev")
        host = os.getenv("POSTGRES_HOST", "localhost")
        port = os.getenv("POSTGRES_PORT", "5432")
        db = os.getenv("POSTGRES_DB", "tripagent")
        return f"postgresql+asyncpg://{user}:{password}@{host}:{port}/{db}"

    sqlite_path = os.getenv("SQLITE_PATH", "tripagent_dev.db")
    return f"sqlite+aiosqlite:///{sqlite_path}"


# ========== 声明式基类 ==========
class Base(DeclarativeBase):
    pass


# ========== 延迟初始化引擎和会话工厂 ==========
_engine = None
_session_factory = None


def _get_engine():
    global _engine
    if _engine is None:
        url = get_database_url()
        use_sqlite = "sqlite" in url
        kwargs = dict(echo=False, pool_pre_ping=True)
        if use_sqlite:
            kwargs.update(connect_args={"check_same_thread": False}, pool_size=1, max_overflow=0)
        else:
            kwargs.update(pool_size=10, max_overflow=20, pool_recycle=3600)
        _engine = create_async_engine(url, **kwargs)
    return _engine


def _get_session_factory():
    global _session_factory
    if _session_factory is None:
        _session_factory = async_sessionmaker(
            _get_engine(), class_=AsyncSession, expire_on_commit=False
        )
    return _session_factory


# ========== FastAPI 依赖注入 ==========
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI Depends: 注入数据库会话"""
    async with _get_session_factory()() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


async def init_db():
    """初始化数据库 — 创建所有表"""
    async with _get_engine().begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def close_db():
    """关闭数据库连接"""
    global _engine
    if _engine is not None:
        await _engine.dispose()
        _engine = None
