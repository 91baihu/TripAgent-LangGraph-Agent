"""数据库配置 — SQLAlchemy async engine + session factory"""

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

    优先级: DATABASE_URL > POSTGRES_URL > 独立 POSTGRES_* 变量
    """
    # 直接使用完整 URL（如 Heroku/Railway 等平台）
    database_url = os.getenv("DATABASE_URL") or os.getenv("POSTGRES_URL")
    if database_url:
        # 确保使用 asyncpg 驱动
        if "asyncpg" not in database_url:
            database_url = database_url.replace("postgresql://", "postgresql+asyncpg://")
            database_url = database_url.replace("postgres://", "postgresql+asyncpg://")
        return database_url

    # 从独立变量构建
    user = os.getenv("POSTGRES_USER", "tripagent")
    password = os.getenv("POSTGRES_PASSWORD", "tripagent_dev")
    host = os.getenv("POSTGRES_HOST", "localhost")
    port = os.getenv("POSTGRES_PORT", "5432")
    db = os.getenv("POSTGRES_DB", "tripagent")

    return f"postgresql+asyncpg://{user}:{password}@{host}:{port}/{db}"


# 引擎（模块加载时不连接，延迟到首次请求）
DATABASE_URL = get_database_url()

engine = create_async_engine(
    DATABASE_URL,
    echo=False,                # SQL 日志（dev 可开 True）
    pool_size=10,              # 连接池大小
    max_overflow=20,           # 额外溢出连接
    pool_pre_ping=True,        # 连接前检查可用性
    pool_recycle=3600,         # 1 小时回收连接
)

# Session 工厂
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


# ========== 声明式基类 ==========
class Base(DeclarativeBase):
    pass


# ========== FastAPI 依赖注入 ==========
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI Depends: 注入数据库会话"""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


async def init_db():
    """初始化数据库 — 创建所有表"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def close_db():
    """关闭数据库连接"""
    await engine.dispose()
