"""会话路由 — 聊天历史 CRUD"""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request, Header
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_db
from ..auth import get_optional_user, get_current_user
from ..services.session_service import session_service

router = APIRouter()


class UpdateSessionRequest(BaseModel):
    title: Optional[str] = Field(None, max_length=255)
    city: Optional[str] = Field(None, max_length=100)
    status: Optional[str] = Field(None, pattern="^(active|archived)$")


# ========== 会话列表 ==========
@router.get("/sessions")
async def list_sessions(
    req: Request,
    db: AsyncSession = Depends(get_db),
    current_user: Optional[dict] = Depends(get_optional_user),
    x_device_fingerprint: Optional[str] = Header(None, alias="X-Device-Fingerprint"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=50),
):
    """获取历史会话列表

    登录用户返回其所有会话，游客返回设备绑定会话。
    """
    user_id = current_user.get("sub") if current_user else None
    return await session_service.list_sessions(
        db,
        user_id=user_id,
        device_fingerprint=x_device_fingerprint,
        page=page,
        page_size=page_size,
    )


# ========== 获取单个会话 ==========
@router.get("/sessions/{session_id}")
async def get_session(
    session_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: Optional[dict] = Depends(get_optional_user),
):
    """获取单个会话详情"""
    user_id = current_user.get("sub") if current_user else None
    session = await session_service.get_session(db, session_id, user_id)
    if session is None:
        raise HTTPException(status_code=404, detail="会话不存在")

    return {
        "id": session.id,
        "title": session.title,
        "city": session.city,
        "status": session.status,
        "created_at": session.created_at.isoformat() if session.created_at else None,
        "updated_at": session.updated_at.isoformat() if session.updated_at else None,
    }


# ========== 获取会话消息 ==========
@router.get("/sessions/{session_id}/messages")
async def get_session_messages(
    session_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: Optional[dict] = Depends(get_optional_user),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
):
    """获取会话的所有消息（按时间排序）"""
    user_id = current_user.get("sub") if current_user else None

    # 验证会话存在且属于当前用户
    session = await session_service.get_session(db, session_id, user_id)
    if session is None:
        raise HTTPException(status_code=404, detail="会话不存在")

    return await session_service.get_messages(
        db, session_id, page=page, page_size=page_size
    )


# ========== 更新会话 ==========
@router.patch("/sessions/{session_id}")
async def update_session(
    session_id: str,
    body: UpdateSessionRequest,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """更新会话标题或状态（需登录）"""
    session = await session_service.update_session(
        db,
        session_id,
        title=body.title,
        city=body.city,
        status=body.status,
    )
    if session is None:
        raise HTTPException(status_code=404, detail="会话不存在")

    return {
        "id": session.id,
        "title": session.title,
        "city": session.city,
        "status": session.status,
    }


# ========== 删除会话 ==========
@router.delete("/sessions/{session_id}", status_code=204)
async def delete_session(
    session_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """删除会话及其所有消息"""
    deleted = await session_service.delete_session(
        db, session_id, user_id=current_user.get("sub")
    )
    if not deleted:
        raise HTTPException(status_code=404, detail="会话不存在")

    return None  # 204 No Content
