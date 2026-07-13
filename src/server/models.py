"""SQLAlchemy ORM 模型 — 兼容 PostgreSQL 和 SQLite"""

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
from sqlalchemy.types import TypeDecorator, CHAR
from sqlalchemy.orm import relationship

from .database import Base


# ========== 方言兼容类型 ==========
class UniversalUUID(TypeDecorator):
    """跨数据库 UUID 类型：PostgreSQL 使用原生 UUID，SQLite 使用 String(36)"""
    impl = CHAR(36)
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == "postgresql":
            from sqlalchemy.dialects.postgresql import UUID as PG_UUID
            return dialect.type_descriptor(PG_UUID())
        else:
            return dialect.type_descriptor(String(36))


def uuid4_str() -> str:
    """生成 UUID4 字符串"""
    return str(uuid.uuid4())


def utcnow() -> datetime:
    """UTC 当前时间"""
    return datetime.now(timezone.utc)


# ========== 用户表 ==========
class User(Base):
    __tablename__ = "users"

    id = Column(UniversalUUID(), primary_key=True, default=uuid4_str)
    email = Column(String(255), unique=True, nullable=False, index=True)
    phone = Column(String(20), default="", index=True)      # 手机号（支持手机号登录）
    nickname = Column(String(100), default="")
    avatar_url = Column(Text, default="")
    password_hash = Column(String(255), default="")
    oauth_provider = Column(String(50), default="")       # google | wechat | github
    oauth_id = Column(String(255), default="")
    role = Column(String(20), default="free")             # free | pro | family | admin
    is_active = Column(Boolean, default=True)
    # 商业化扩展字段（阶段一）
    credits_balance = Column(Integer, default=0)          # 当前剩余额度
    monthly_quota = Column(Integer, default=0)            # 当月总配额
    quota_reset_at = Column(DateTime(timezone=True), nullable=True)  # 配额重置时间
    created_at = Column(DateTime(timezone=True), default=utcnow)
    updated_at = Column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

    # 关系
    trips = relationship("Trip", back_populates="user", cascade="all, delete-orphan")
    preferences = relationship("UserPreference", back_populates="user", uselist=False, cascade="all, delete-orphan")
    credits = relationship("UserCredit", back_populates="user", uselist=False, cascade="all, delete-orphan")
    credit_transactions = relationship("CreditTransaction", back_populates="user", cascade="all, delete-orphan")
    chat_sessions = relationship("ChatSession", back_populates="user", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<User {self.email}>"


# ========== 行程表 ==========
class Trip(Base):
    __tablename__ = "trips"

    id = Column(UniversalUUID(), primary_key=True, default=uuid4_str)
    user_id = Column(UniversalUUID(), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    title = Column(String(255), nullable=False)
    city = Column(String(100), nullable=False, index=True)
    days = Column(Integer, nullable=False, default=3)
    itinerary_json = Column(JSON, nullable=False, default=dict)
    status = Column(String(20), default="draft")           # draft | confirmed | completed | archived
    share_token = Column(String(64), unique=True, nullable=True)
    share_expires_at = Column(DateTime(timezone=True), nullable=True)
    # 商业化 & 导出扩展字段（阶段一）
    raw_markdown = Column(Text, nullable=True)             # Agent 输出原文（用于导出）
    session_id = Column(UniversalUUID(), ForeignKey("chat_sessions.id", ondelete="SET NULL"), nullable=True)  # 关联来源会话
    export_formats = Column(JSON, default=list)            # ['md','pdf','docx'] — 已导出格式记录
    created_at = Column(DateTime(timezone=True), default=utcnow)
    updated_at = Column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

    # 关系
    user = relationship("User", back_populates="trips")
    session = relationship("ChatSession", back_populates="trips", foreign_keys=[session_id])

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

    id = Column(UniversalUUID(), primary_key=True, default=uuid4_str)
    user_id = Column(UniversalUUID(), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
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

    id = Column(UniversalUUID(), primary_key=True, default=uuid4_str)
    user_id = Column(UniversalUUID(), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
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

    id = Column(UniversalUUID(), primary_key=True, default=uuid4_str)
    user_id = Column(UniversalUUID(), ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    budget_level = Column(String(20), default="mid")        # budget | mid | luxury
    travel_style = Column(JSON, default=list)               # ["亲子","文化","户外"]
    favorite_cities = Column(JSON, default=list)
    created_at = Column(DateTime(timezone=True), default=utcnow)
    updated_at = Column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

    # 关系
    user = relationship("User", back_populates="preferences")

    def __repr__(self):
        return f"<UserPreference user={self.user_id}>"


# ========== 游客设备会话表 ==========
class DeviceSession(Base):
    """游客设备会话 — 设备指纹绑定免费额度"""
    __tablename__ = "device_sessions"

    id = Column(UniversalUUID(), primary_key=True, default=uuid4_str)
    fingerprint = Column(String(128), unique=True, nullable=False, index=True)
    remaining_quota = Column(Integer, default=1)            # 剩余免费次数
    total_used = Column(Integer, default=0)                 # 累计已用
    user_agent = Column(Text, nullable=True)                # 辅助识别
    ip_address = Column(String(45), nullable=True)          # 最后活跃 IP
    created_at = Column(DateTime(timezone=True), default=utcnow)
    last_used_at = Column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

    # 关系
    chat_sessions = relationship("ChatSession", back_populates="device", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<DeviceSession fp={self.fingerprint[:12]}... quota={self.remaining_quota}>"


# ========== 聊天会话表 ==========
class ChatSession(Base):
    """聊天会话 — 用户或游客的一次对话"""
    __tablename__ = "chat_sessions"

    id = Column(UniversalUUID(), primary_key=True, default=uuid4_str)
    user_id = Column(UniversalUUID(), ForeignKey("users.id", ondelete="CASCADE"), nullable=True, index=True)
    device_id = Column(UniversalUUID(), ForeignKey("device_sessions.id", ondelete="SET NULL"), nullable=True, index=True)
    title = Column(String(255), default="新的旅程")
    city = Column(String(100), nullable=True)
    status = Column(String(20), default="active")           # active | archived
    created_at = Column(DateTime(timezone=True), default=utcnow)
    updated_at = Column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

    # 关系
    user = relationship("User", back_populates="chat_sessions")
    device = relationship("DeviceSession", back_populates="chat_sessions")
    messages = relationship("ChatMessage", back_populates="session", cascade="all, delete-orphan")
    trips = relationship("Trip", back_populates="session", foreign_keys="Trip.session_id")

    def __repr__(self):
        return f"<ChatSession {self.title}>"


# ========== 聊天消息表 ==========
class ChatMessage(Base):
    """聊天消息 — 会话中的一条消息"""
    __tablename__ = "chat_messages"

    id = Column(UniversalUUID(), primary_key=True, default=uuid4_str)
    session_id = Column(UniversalUUID(), ForeignKey("chat_sessions.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(UniversalUUID(), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    role = Column(String(20), nullable=False)               # user | assistant | tool
    content = Column(Text, default="")                      # 文本内容
    tool_name = Column(String(100), nullable=True)          # 工具名（role=tool 时）
    tool_args = Column(JSON, default=dict)                  # 工具参数
    tool_result = Column(Text, nullable=True)               # 工具返回
    token_count = Column(Integer, default=0)                # 估算 token 消耗
    message_index = Column(Integer, default=0)              # 会话内排序
    created_at = Column(DateTime(timezone=True), default=utcnow)

    # 关系
    session = relationship("ChatSession", back_populates="messages")

    __table_args__ = (
        Index("idx_messages_session_index", "session_id", "message_index"),
    )

    def __repr__(self):
        return f"<ChatMessage [{self.role}] {self.content[:50]}...>"


# ========== 用户额度表 ==========
class UserCredit(Base):
    """用户额度 — 登录用户的配额管理"""
    __tablename__ = "user_credits"

    id = Column(UniversalUUID(), primary_key=True, default=uuid4_str)
    user_id = Column(UniversalUUID(), ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    total_purchased = Column(Integer, default=0)             # 累计购买额度
    used_this_month = Column(Integer, default=0)             # 当月已用
    expires_at = Column(DateTime(timezone=True), nullable=True)  # 额度过期时间（月付）
    created_at = Column(DateTime(timezone=True), default=utcnow)
    updated_at = Column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

    # 关系
    user = relationship("User", back_populates="credits")

    def __repr__(self):
        return f"<UserCredit user={self.user_id} used={self.used_this_month}>"


# ========== 额度流水表 ==========
class CreditTransaction(Base):
    """额度流水 — 每次额度变动记录"""
    __tablename__ = "credit_transactions"

    id = Column(UniversalUUID(), primary_key=True, default=uuid4_str)
    user_id = Column(UniversalUUID(), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    type = Column(String(20), nullable=False)               # earn | consume | refund | gift
    amount = Column(Integer, nullable=False)                # 变动数量
    balance_after = Column(Integer, nullable=False)         # 变动后余额
    description = Column(String(500), nullable=True)        # 说明
    session_id = Column(UniversalUUID(), ForeignKey("chat_sessions.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime(timezone=True), default=utcnow)

    # 关系
    user = relationship("User", back_populates="credit_transactions")

    __table_args__ = (
        Index("idx_credit_tx_user_time", "user_id", "created_at"),
    )

    def __repr__(self):
        return f"<CreditTransaction [{self.type}] {self.amount}>"


# ========== 购买订单表 ==========
class PurchaseOrder(Base):
    """购买订单 — 套餐购买记录"""
    __tablename__ = "purchase_orders"

    id = Column(UniversalUUID(), primary_key=True, default=uuid4_str)
    user_id = Column(UniversalUUID(), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    plan_id = Column(String(50), nullable=False)            # free | pro_monthly | pro_yearly | family
    amount_cents = Column(Integer, nullable=False)          # 金额（分）
    credits_purchased = Column(Integer, nullable=False)     # 购买额度数
    status = Column(String(20), default="pending")          # pending | paid | cancelled | refunded
    payment_method = Column(String(50), nullable=True)      # alipay | wechat | stripe | manual
    payment_ref = Column(String(255), nullable=True)        # 第三方支付流水号
    paid_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=utcnow)

    def __repr__(self):
        return f"<PurchaseOrder [{self.plan_id}] {self.status}>"
