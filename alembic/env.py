"""Alembic 环境配置 — 异步 PostgreSQL 迁移"""

import asyncio
import os
from logging.config import fileConfig

from alembic import context
from sqlalchemy import pool
from sqlalchemy.ext.asyncio import create_async_engine

# Alembic Config 对象
config = context.config

# 设置日志
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# ===== 数据库 URL =====
# 优先使用环境变量，否则使用 alembic.ini 中的配置
def get_url() -> str:
    url = os.getenv("DATABASE_URL") or os.getenv("POSTGRES_URL")
    if url:
        if "asyncpg" not in url:
            url = url.replace("postgresql://", "postgresql+asyncpg://")
            url = url.replace("postgres://", "postgresql+asyncpg://")
        return url

    # 从独立变量构建
    user = os.getenv("POSTGRES_USER", "tripagent")
    password = os.getenv("POSTGRES_PASSWORD", "tripagent_dev")
    host = os.getenv("POSTGRES_HOST", "localhost")
    port = os.getenv("POSTGRES_PORT", "5432")
    db = os.getenv("POSTGRES_DB", "tripagent")
    return f"postgresql+asyncpg://{user}:{password}@{host}:{port}/{db}"


# ===== 元数据 =====
# 导入所有 ORM 模型，确保 Base.metadata 包含所有表
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from server.database import Base  # noqa: E402
from server.models import (  # noqa: F401
    User,
    Trip,
    ToolCallLog,
    ApiKey,
    UserPreference,
)

target_metadata = Base.metadata

# 设置连接 URL
config.set_main_option("sqlalchemy.url", get_url())


# ===== 迁移执行 =====
def run_migrations_offline() -> None:
    """离线模式 — 生成 SQL 脚本，不连接数据库"""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection):
    context.configure(connection=connection, target_metadata=target_metadata)
    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    """在线模式 — 连接数据库并执行迁移"""
    connectable = create_async_engine(
        get_url(),
        poolclass=pool.NullPool,
    )

    async with connectable.begin() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


def run_migrations_online() -> None:
    """在线模式入口"""
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
