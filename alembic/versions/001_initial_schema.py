"""Initial schema — users, trips, tool_call_logs, api_keys, user_preferences

Revision ID: 001
Revises: None
Create Date: 2026-07-08
"""

from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 启用扩展
    op.execute("CREATE EXTENSION IF NOT EXISTS \"uuid-ossp\"")
    op.execute("CREATE EXTENSION IF NOT EXISTS \"pgcrypto\"")

    # ===== users =====
    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=False), primary_key=True),
        sa.Column("email", sa.String(255), unique=True, nullable=False),
        sa.Column("nickname", sa.String(100), default=""),
        sa.Column("avatar_url", sa.Text, default=""),
        sa.Column("password_hash", sa.String(255), default=""),
        sa.Column("oauth_provider", sa.String(50), default=""),
        sa.Column("oauth_id", sa.String(255), default=""),
        sa.Column("role", sa.String(20), default="free"),
        sa.Column("is_active", sa.Boolean, default=True),
        sa.Column("created_at", sa.DateTime(timezone=True)),
        sa.Column("updated_at", sa.DateTime(timezone=True)),
    )
    op.create_index("idx_users_email", "users", ["email"])

    # ===== trips =====
    op.create_table(
        "trips",
        sa.Column("id", postgresql.UUID(as_uuid=False), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=False),
                  sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("city", sa.String(100), nullable=False),
        sa.Column("days", sa.Integer, nullable=False, default=3),
        sa.Column("itinerary_json", sa.JSON, nullable=False, default=dict),
        sa.Column("status", sa.String(20), default="draft"),
        sa.Column("share_token", sa.String(64), unique=True, nullable=True),
        sa.Column("share_expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True)),
        sa.Column("updated_at", sa.DateTime(timezone=True)),
    )
    op.create_index("idx_trips_user_status", "trips", ["user_id", "status"])
    op.create_index("idx_trips_share", "trips", ["share_token"])
    op.create_index("idx_trips_city", "trips", ["city"])

    # ===== tool_call_logs =====
    op.create_table(
        "tool_call_logs",
        sa.Column("id", postgresql.UUID(as_uuid=False), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=False),
                  sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("session_id", sa.String(64), nullable=False),
        sa.Column("tool_name", sa.String(100), nullable=False),
        sa.Column("input_json", sa.JSON, nullable=False, default=dict),
        sa.Column("output_json", sa.JSON, nullable=True),
        sa.Column("latency_ms", sa.Integer, nullable=True),
        sa.Column("token_count", sa.Integer, default=0),
        sa.Column("error_message", sa.Text, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True)),
    )
    op.create_index("idx_tool_logs_session_tool", "tool_call_logs", ["session_id", "tool_name"])
    op.create_index("idx_tool_logs_created", "tool_call_logs", ["created_at"])

    # ===== api_keys =====
    op.create_table(
        "api_keys",
        sa.Column("id", postgresql.UUID(as_uuid=False), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=False),
                  sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("key_hash", sa.String(255), unique=True, nullable=False),
        sa.Column("key_prefix", sa.String(8), nullable=False),
        sa.Column("name", sa.String(100), default=""),
        sa.Column("call_limit_per_day", sa.Integer, default=500),
        sa.Column("call_count_today", sa.Integer, default=0),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("is_active", sa.Boolean, default=True),
        sa.Column("created_at", sa.DateTime(timezone=True)),
    )
    op.create_index("idx_api_keys_user", "api_keys", ["user_id"])

    # ===== user_preferences =====
    op.create_table(
        "user_preferences",
        sa.Column("id", postgresql.UUID(as_uuid=False), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=False),
                  sa.ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False),
        sa.Column("budget_level", sa.String(20), default="mid"),
        sa.Column("travel_style", sa.JSON, default=list),
        sa.Column("favorite_cities", sa.JSON, default=list),
        sa.Column("created_at", sa.DateTime(timezone=True)),
        sa.Column("updated_at", sa.DateTime(timezone=True)),
    )

    # ===== updated_at 触发器 =====
    op.execute("""
        CREATE OR REPLACE FUNCTION update_updated_at()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.updated_at = NOW();
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
    """)
    for table in ["users", "trips", "user_preferences"]:
        op.execute(f"""
            CREATE TRIGGER trg_{table}_updated
                BEFORE UPDATE ON {table}
                FOR EACH ROW EXECUTE FUNCTION update_updated_at();
        """)


def downgrade() -> None:
    """回滚所有迁移"""
    for table in ["user_preferences", "api_keys", "tool_call_logs", "trips", "users"]:
        op.execute(f"DROP TRIGGER IF EXISTS trg_{table}_updated ON {table}")
    op.execute("DROP FUNCTION IF EXISTS update_updated_at()")
    op.drop_table("user_preferences")
    op.drop_table("api_keys")
    op.drop_table("tool_call_logs")
    op.drop_table("trips")
    op.drop_table("users")
