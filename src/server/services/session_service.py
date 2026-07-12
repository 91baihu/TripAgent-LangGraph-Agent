"""会话与消息持久化服务

提供聊天会话的完整生命周期管理：
- 创建/查询/删除会话
- 消息持久化（逐条写入）
- 游客会话迁移到登录用户
"""

import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, func, update

from ..models import ChatSession, ChatMessage, DeviceSession


class SessionService:
    """会话与消息持久化服务"""

    # ========== 会话管理 ==========

    async def get_or_create_session(
        self,
        db: AsyncSession,
        user_id: Optional[str] = None,
        device_fingerprint: Optional[str] = None,
        city: Optional[str] = None,
        title: str = "新的旅程",
    ) -> ChatSession:
        """获取最近的活跃会话，或创建新会话

        优先查找用户在 30 分钟内的活跃会话，避免每次对话创建新会话。
        找不到则创建新会话。

        Args:
            db: 数据库会话
            user_id: 登录用户 ID
            device_fingerprint: 设备指纹（游客场景）
            city: 目的地城市
            title: 会话标题

        Returns:
            ChatSession 实例
        """
        # ── 查找最近的活跃会话 ──
        query = select(ChatSession).where(
            ChatSession.status == "active"
        )

        if user_id:
            query = query.where(ChatSession.user_id == user_id)
        elif device_fingerprint:
            # 通过 device 查找
            device_result = await db.execute(
                select(DeviceSession).where(
                    DeviceSession.fingerprint == device_fingerprint
                )
            )
            device = device_result.scalar_one_or_none()
            if device:
                query = query.where(ChatSession.device_id == device.id)
            else:
                # 无设备记录 → 直接创建新会话
                return await self.create_session(
                    db, user_id, device_fingerprint, city, title
                )
        else:
            # 无任何标识 → 直接创建
            return await self.create_session(
                db, user_id, device_fingerprint, city, title
            )

        query = query.order_by(desc(ChatSession.updated_at)).limit(1)
        result = await db.execute(query)
        session = result.scalar_one_or_none()

        if session:
            # 更新城市和标题
            if city and not session.city:
                session.city = city
            session.updated_at = datetime.now(timezone.utc)
            await db.flush()
            return session

        return await self.create_session(
            db, user_id, device_fingerprint, city, title
        )

    async def create_session(
        self,
        db: AsyncSession,
        user_id: Optional[str] = None,
        device_fingerprint: Optional[str] = None,
        city: Optional[str] = None,
        title: str = "新的旅程",
    ) -> ChatSession:
        """创建新会话"""
        # 解析 device_id
        device_id = None
        if device_fingerprint:
            device_result = await db.execute(
                select(DeviceSession).where(
                    DeviceSession.fingerprint == device_fingerprint
                )
            )
            device = device_result.scalar_one_or_none()
            if device:
                device_id = device.id

        session = ChatSession(
            id=str(uuid.uuid4()),
            user_id=user_id,
            device_id=device_id,
            title=title,
            city=city,
            status="active",
        )
        db.add(session)
        await db.flush()
        return session

    async def list_sessions(
        self,
        db: AsyncSession,
        user_id: Optional[str] = None,
        device_fingerprint: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> dict:
        """获取会话列表（分页）

        Args:
            user_id: 登录用户 ID
            device_fingerprint: 设备指纹（游客场景）
            page: 页码（从 1 开始）
            page_size: 每页数量

        Returns:
            {"sessions": [...], "total": int, "page": int, "page_size": int}
        """
        query = select(ChatSession)

        if user_id:
            query = query.where(ChatSession.user_id == user_id)
        elif device_fingerprint:
            device_result = await db.execute(
                select(DeviceSession).where(
                    DeviceSession.fingerprint == device_fingerprint
                )
            )
            device = device_result.scalar_one_or_none()
            if device:
                query = query.where(ChatSession.device_id == device.id)
            else:
                return {"sessions": [], "total": 0, "page": page, "page_size": page_size}

        # 统计总数
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await db.execute(count_query)
        total = total_result.scalar() or 0

        # 分页查询
        query = (
            query
            .order_by(desc(ChatSession.updated_at))
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        result = await db.execute(query)
        sessions = result.scalars().all()

        return {
            "sessions": [
                {
                    "id": s.id,
                    "title": s.title,
                    "city": s.city,
                    "status": s.status,
                    "message_count": 0,  # 后续可优化为 JOIN 查询
                    "created_at": s.created_at.isoformat() if s.created_at else None,
                    "updated_at": s.updated_at.isoformat() if s.updated_at else None,
                }
                for s in sessions
            ],
            "total": total,
            "page": page,
            "page_size": page_size,
        }

    async def get_session(
        self,
        db: AsyncSession,
        session_id: str,
        user_id: Optional[str] = None,
    ) -> Optional[ChatSession]:
        """获取单个会话详情（可选的用户权限校验）"""
        query = select(ChatSession).where(ChatSession.id == session_id)
        if user_id:
            query = query.where(ChatSession.user_id == user_id)

        result = await db.execute(query)
        return result.scalar_one_or_none()

    async def update_session(
        self,
        db: AsyncSession,
        session_id: str,
        title: Optional[str] = None,
        city: Optional[str] = None,
        status: Optional[str] = None,
    ) -> Optional[ChatSession]:
        """更新会话标题/城市/状态"""
        result = await db.execute(
            select(ChatSession).where(ChatSession.id == session_id)
        )
        session = result.scalar_one_or_none()
        if session is None:
            return None

        if title is not None:
            session.title = title
        if city is not None:
            session.city = city
        if status is not None:
            session.status = status

        session.updated_at = datetime.now(timezone.utc)
        await db.flush()
        return session

    async def delete_session(
        self,
        db: AsyncSession,
        session_id: str,
        user_id: Optional[str] = None,
    ) -> bool:
        """删除会话（级联删除所有消息）"""
        query = select(ChatSession).where(ChatSession.id == session_id)
        if user_id:
            query = query.where(ChatSession.user_id == user_id)

        result = await db.execute(query)
        session = result.scalar_one_or_none()
        if session is None:
            return False

        await db.delete(session)
        await db.flush()
        return True

    # ========== 消息管理 ==========

    async def save_message(
        self,
        db: AsyncSession,
        session_id: str,
        role: str,
        content: str = "",
        user_id: Optional[str] = None,
        tool_name: Optional[str] = None,
        tool_args: Optional[dict] = None,
        tool_result: Optional[str] = None,
        token_count: int = 0,
    ) -> ChatMessage:
        """保存一条消息到数据库

        Args:
            session_id: 所属会话 ID
            role: 消息角色 (user/assistant/tool)
            content: 文本内容
            user_id: 发送者用户 ID
            tool_name: 工具名（role=tool 时）
            tool_args: 工具参数（role=tool 时）
            tool_result: 工具返回结果
            token_count: 估算 token 消耗

        Returns:
            新创建的 ChatMessage 实例
        """
        # 获取当前会话的最大 message_index
        count_result = await db.execute(
            select(func.coalesce(func.max(ChatMessage.message_index), -1))
            .where(ChatMessage.session_id == session_id)
        )
        max_index = count_result.scalar() or -1

        msg = ChatMessage(
            id=str(uuid.uuid4()),
            session_id=session_id,
            user_id=user_id,
            role=role,
            content=content,
            tool_name=tool_name,
            tool_args=tool_args or {},
            tool_result=tool_result,
            token_count=token_count,
            message_index=max_index + 1,
        )
        db.add(msg)
        await db.flush()
        return msg

    async def update_tool_result(
        self,
        db: AsyncSession,
        session_id: str,
        tool_name: str,
        result: str,
    ):
        """更新最近一条 tool 消息的 result 字段

        SSE 流程中 tool_call 先于 tool_result 发送，需要用此方法回填结果。
        """
        # 查找该 session 下最近一条 role=tool 且 tool_result 为空的记录
        result_row = await db.execute(
            select(ChatMessage)
            .where(
                ChatMessage.session_id == session_id,
                ChatMessage.role == "tool",
                ChatMessage.tool_name == tool_name,
                ChatMessage.tool_result.is_(None),
            )
            .order_by(desc(ChatMessage.message_index))
            .limit(1)
        )
        msg = result_row.scalar_one_or_none()
        if msg:
            msg.tool_result = result[:2000]  # 截断过长内容
            await db.flush()

    async def get_messages(
        self,
        db: AsyncSession,
        session_id: str,
        page: int = 1,
        page_size: int = 50,
    ) -> dict:
        """获取会话的消息列表（分页，按 message_index 排序）

        Returns:
            {"messages": [...], "total": int, "page": int, "page_size": int}
        """
        # 统计总数
        count_result = await db.execute(
            select(func.count()).where(ChatMessage.session_id == session_id)
        )
        total = count_result.scalar() or 0

        # 分页查询
        query = (
            select(ChatMessage)
            .where(ChatMessage.session_id == session_id)
            .order_by(ChatMessage.message_index)
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        result = await db.execute(query)
        messages = result.scalars().all()

        return {
            "messages": [
                {
                    "id": m.id,
                    "role": m.role,
                    "content": m.content,
                    "tool_name": m.tool_name,
                    "tool_args": m.tool_args,
                    "tool_result": m.tool_result,
                    "message_index": m.message_index,
                    "created_at": m.created_at.isoformat() if m.created_at else None,
                }
                for m in messages
            ],
            "total": total,
            "page": page,
            "page_size": page_size,
        }

    # ========== 会话迁移 ==========

    async def claim_device_sessions(
        self,
        db: AsyncSession,
        user_id: str,
        device_fingerprint: str,
    ):
        """用户登录后，将设备上的游客会话迁移到用户账户

        登录前的游客会话在注册/登录后自动迁移：
        - chat_sessions.device_id → 改为 user_id
        - chat_messages.user_id → 自动填充
        """
        # 查找设备记录
        device_result = await db.execute(
            select(DeviceSession).where(
                DeviceSession.fingerprint == device_fingerprint
            )
        )
        device = device_result.scalar_one_or_none()
        if device is None:
            return 0

        # 将该设备的所有会话归属到用户
        await db.execute(
            update(ChatSession)
            .where(
                ChatSession.device_id == device.id,
                ChatSession.user_id.is_(None),
            )
            .values(user_id=user_id)
        )

        # 将该设备的所有消息归属到用户
        # 通过子查询实现: 更新属于该设备会话的消息
        session_ids_result = await db.execute(
            select(ChatSession.id).where(
                ChatSession.device_id == device.id
            )
        )
        session_ids = [row[0] for row in session_ids_result.all()]

        if session_ids:
            await db.execute(
                update(ChatMessage)
                .where(
                    ChatMessage.session_id.in_(session_ids),
                    ChatMessage.user_id.is_(None),
                )
                .values(user_id=user_id)
            )

        await db.flush()
        return len(session_ids)


# 全局服务实例
session_service = SessionService()
