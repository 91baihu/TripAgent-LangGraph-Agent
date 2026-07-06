"""SQLAlchemy ORM 模型"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import (
    Column,
    String,
    Integer,
    Boolean,
    DateTime,
    ForeignKey,
    Text,
    JSON,
    Index,
    Float,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from .database import Base


def uuid4_str() -> str:
    """生成 UUID4 字符串"""
    return str(uuid.uuid4())


def utcnow() -> datetime:
    """UTC 当前时间"""
    return datetime.now(timezone.utc)


# ========== 用户表 ==========
class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=False), primary_key=True, default=uuid4_str)
    email = Column(String(255), unique=True, nullable=False, index=True)
    nickname = Column(String(100), default="")
    avatar_url = Column(Text, default="")
    password_hash = Column(String(255), default="")
    oauth_provider = Column(String(50), default="")       # google | wechat | github
    oauth_id = Column(String(255), default="")
    role = Column(String(20), default="free")             # free | pro | family | admin
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), default=utcnow)
    updated_at = Column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

    # 关系
    trips = relationship("Trip", back_populates="user", cascade="all, delete-orphan")
    preferences = relationship("UserPreference", back_populates="user", uselist=False, cascade="all, delete-orphan")

    def __repr__(self):
        return f"<User {self.email}>"


# ========== 行程表 ==========
class Trip(Base):
    __tablename__ = "trips"

    id = Column(UUID(as_uuid=False), primary_key=True, default=uuid4_str)
    user_id = Column(UUID(as_uuid=False), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    title = Column(String(255), nullable=False)
    city = Column(String(100), nullable=False, index=True)
    days = Column(Integer, nullable=False, default=3)
    itinerary_json = Column(JSON, nullable=False, default=dict)
    status = Column(String(20), default="draft")           # draft | confirmed | completed | archived
    share_token = Column(String(64), unique=True, nullable=True)
    share_expires_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=utcnow)
    updated_at = Column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

    # 关系
    user = relationship("User", back_populates="trips")

    # 索引
    __table_args__ = (
        Index("idx_trips_user_status", "user_id", "status"),
        Index("idx_trips_share", "share_token"),
    )

    def __repr__(self):
        return f"<Trip {self.title} [{self.city}]>"


# ========== 工具调用审计表 ==========
class ToolCallLog(Base):
    __tablename__ = "tool_call_logs"

    id = Column(UUID(as_uuid=False), primary_key=True, default=uuid4_str)
    user_id = Column(UUID(as_uuid=False), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    session_id = Column(String(64), nullable=False, index=True)
    tool_name = Column(String(100), nullable=False, index=True)
    input_json = Column(JSON, nullable=False, default=dict)
    output_json = Column(JSON, nullable=True)
    latency_ms = Column(Integer, nullable=True)
    token_count = Column(Integer, default=0)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=utcnow, index=True)

    __table_args__ = (
        Index("idx_tool_logs_session_tool", "session_id", "tool_name"),
    )

    def __repr__(self):
        return f"<ToolCallLog {self.tool_name}>"


# ========== API Key 表（B2B 客户） ==========
class ApiKey(Base):
    __tablename__ = "api_keys"

    id = Column(UUID(as_uuid=False), primary_key=True, default=uuid4_str)
    user_id = Column(UUID(as_uuid=False), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    key_hash = Column(String(255), unique=True, nullable=False)
    key_prefix = Column(String(8), nullable=False)         # "ta_ab12..."
    name = Column(String(100), default="")
    call_limit_per_day = Column(Integer, default=500)
    call_count_today = Column(Integer, default=0)
    expires_at = Column(DateTime(timezone=True), nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), default=utcnow)

    def __repr__(self):
        return f"<ApiKey {self.key_prefix}***>"


# ========== 用户偏好表 ==========
class UserPreference(Base):
    __tablename__ = "user_preferences"

    id = Column(UUID(as_uuid=False), primary_key=True, default=uuid4_str)
    user_id = Column(UUID(as_uuid=False), ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    budget_level = Column(String(20), default="mid")        # budget | mid | luxury
    travel_style = Column(JSON, default=list)               # ["亲子","文化","户外"]
    favorite_cities = Column(JSON, default=list)
    created_at = Column(DateTime(timezone=True), default=utcnow)
    updated_at = Column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

    # 关系
    user = relationship("User", back_populates="preferences")

    def __repr__(self):
        return f"<UserPreference user={self.user_id}>"
