"""认证路由 — 注册/登录/刷新令牌 (PostgreSQL)"""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, status, Header
from typing import Optional
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..auth import (
    hash_password,
    verify_password,
    create_access_token,
    create_refresh_token,
    verify_token,
    get_current_user,
    bearer_scheme,
)
from ..database import get_db
from ..models import User
from ..services.credit_service import credit_service
from ..services.session_service import session_service

router = APIRouter(prefix="/auth", tags=["认证"])


# ========== 请求模型 ==========
class RegisterRequest(BaseModel):
    email: str = Field(..., min_length=5, max_length=255, pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
    password: str = Field(..., min_length=8, max_length=72)
    nickname: str = Field(default="", max_length=50)


class LoginRequest(BaseModel):
    email: str = Field(..., min_length=5, max_length=255)
    password: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int  # 秒


class RefreshRequest(BaseModel):
    refresh_token: str


# ========== 辅助函数 ==========
async def _get_user_by_email(db: AsyncSession, email: str) -> User | None:
    """通过邮箱查询用户"""
    result = await db.execute(select(User).where(User.email == email))
    return result.scalar_one_or_none()


async def _get_user_by_id(db: AsyncSession, user_id: str) -> User | None:
    """通过 ID 查询用户"""
    result = await db.execute(select(User).where(User.id == user_id))
    return result.scalar_one_or_none()


# ========== 路由 ==========
@router.post("/register", status_code=201)
async def register(req: RegisterRequest, db: AsyncSession = Depends(get_db)):
    """用户注册"""
    # 检查邮箱是否已注册
    existing = await _get_user_by_email(db, req.email)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="该邮箱已被注册",
        )

    user = User(
        id=str(uuid.uuid4()),
        email=req.email,
        nickname=req.nickname or req.email.split("@")[0],
        password_hash=hash_password(req.password),
        role="free",
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)

    # 阶段二：新用户注册赠送 10 次试用额度
    try:
        await credit_service.grant_trial_credits(db, user.id)
        await db.commit()
    except Exception:
        # 赠送失败不影响注册流程
        pass

    access_token = create_access_token(str(user.id), user.role)
    refresh_token = create_refresh_token(str(user.id))

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=15 * 60,  # 15 分钟
    )


@router.post("/login", response_model=TokenResponse)
async def login(
    req: LoginRequest,
    db: AsyncSession = Depends(get_db),
    x_device_fingerprint: Optional[str] = Header(None, alias="X-Device-Fingerprint"),
):
    """用户登录 — 登录后自动迁移设备上的游客会话"""
    user = await _get_user_by_email(db, req.email)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="邮箱或密码错误",
        )

    if not verify_password(req.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="邮箱或密码错误",
        )

    # 阶段三：登录后迁移游客设备会话到用户账户
    if x_device_fingerprint:
        try:
            await session_service.claim_device_sessions(
                db, user.id, x_device_fingerprint
            )
            await db.commit()
        except Exception:
            pass  # 迁移失败不影响登录

    access_token = create_access_token(str(user.id), user.role)
    refresh_token = create_refresh_token(str(user.id))

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=15 * 60,
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(req: RefreshRequest, db: AsyncSession = Depends(get_db)):
    """刷新访问令牌"""
    payload = verify_token(req.refresh_token)

    if payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="令牌类型错误，需要 refresh token",
        )

    user_id = payload["sub"]

    # 确认用户仍存在
    user = await _get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户不存在",
        )

    new_access = create_access_token(user_id, user.role)
    new_refresh = create_refresh_token(user_id)

    return TokenResponse(
        access_token=new_access,
        refresh_token=new_refresh,
        expires_in=15 * 60,
    )


@router.get("/me")
async def get_me(
    user_payload: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """获取当前用户信息"""
    user = await _get_user_by_id(db, user_payload["sub"])
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")

    return {
        "id": user.id,
        "email": user.email,
        "nickname": user.nickname,
        "role": user.role,
    }
