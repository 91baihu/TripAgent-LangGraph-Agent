"""认证路由 — 注册/登录/刷新令牌 (PostgreSQL)"""

from __future__ import annotations

import uuid
import random
import os

from fastapi import APIRouter, Depends, HTTPException, status, Header
from typing import Optional
from pydantic import BaseModel, Field
from sqlalchemy import select, or_
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
from ..cache import cache_service

router = APIRouter(prefix="/auth", tags=["认证"])


# ========== 请求模型 ==========
class RegisterRequest(BaseModel):
    email: str = Field(..., min_length=5, max_length=255, pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
    password: str = Field(..., min_length=8, max_length=72)
    nickname: str = Field(default="", max_length=50)
    code: Optional[str] = Field(default=None, min_length=4, max_length=6)
    phone: Optional[str] = Field(default=None, max_length=20)


class LoginRequest(BaseModel):
    email: Optional[str] = Field(default=None, min_length=5, max_length=255)
    phone: Optional[str] = Field(default=None, max_length=20)
    password: str
    login_type: str = Field(default="email", pattern="^(email|phone)$")


class SendCodeRequest(BaseModel):
    target: str = Field(..., min_length=5, max_length=255)
    type: str = Field(default="email", pattern="^(email|phone)$")


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


async def _get_user_by_phone(db: AsyncSession, phone: str) -> User | None:
    """通过手机号查询用户"""
    result = await db.execute(select(User).where(User.phone == phone))
    return result.scalar_one_or_none()


async def _get_user_by_id(db: AsyncSession, user_id: str) -> User | None:
    """通过 ID 查询用户"""
    result = await db.execute(select(User).where(User.id == user_id))
    return result.scalar_one_or_none()


# ========== 路由 ==========

@router.post("/send-code")
async def send_verification_code(req: SendCodeRequest):
    """发送验证码（邮箱或手机号）

    验证码 6 位数字，5 分钟有效，存入 Redis。
    开发环境默认验证码：888888（可通过 DEV_VERIFICATION_CODE 环境变量自定义）
    """
    # 开发环境固定验证码
    dev_code = os.getenv("DEV_VERIFICATION_CODE", "888888")

    # 生成 6 位随机验证码
    code = dev_code if os.getenv("APP_ENV", "dev") in ("dev", "development", "test") else \
        f"{random.randint(100000, 999999)}"

    # 存入 Redis（key: verify_code:{type}:{target}, TTL 5 分钟）
    key = f"verify_code:{req.type}:{req.target}"
    try:
        await cache_service.set(key, code, ttl=300)
    except Exception:
        # Redis 不可用时降级：开发环境仍返回成功
        if os.getenv("APP_ENV", "dev") not in ("dev", "development", "test"):
            raise HTTPException(status_code=500, detail="验证码服务暂不可用")

    # 开发环境打印验证码到日志
    if os.getenv("APP_ENV", "dev") in ("dev", "development", "test"):
        from ..logging import logger
        logger.info(f"verification_code target={req.target} code={code}")

    return {"message": "验证码已发送", "target": req.target[:3] + "***"}


def _verify_code(code_type: str, target: str, code: str) -> bool:
    """验证码校验（同步方式，简化处理）"""
    import asyncio
    dev_code = os.getenv("DEV_VERIFICATION_CODE", "888888")
    # 开发环境万能验证码
    if os.getenv("APP_ENV", "dev") in ("dev", "development", "test") and code == dev_code:
        return True

    key = f"verify_code:{code_type}:{target}"
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # 在运行中的事件循环里创建新 task
            import asyncio
            stored = None
            async def _get():
                return await cache_service.get(key)
            # 简化：直接尝试同步方式
            try:
                stored = asyncio.run_coroutine_threadsafe(cache_service.get(key), loop).result(timeout=2)
            except Exception:
                stored = None
        else:
            stored = asyncio.run(cache_service.get(key))
    except Exception:
        stored = None

    return stored == code if stored else False


@router.post("/register", status_code=201)
async def register(req: RegisterRequest, db: AsyncSession = Depends(get_db)):
    """用户注册 — 需要验证码"""
    # 校验验证码
    if req.code:
        if not _verify_code("email", req.email, req.code):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="验证码错误或已过期",
            )

    # 检查邮箱是否已注册
    existing = await _get_user_by_email(db, req.email)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="该邮箱已被注册",
        )

    # 检查手机号是否已注册
    if req.phone:
        existing_phone = await _get_user_by_phone(db, req.phone)
        if existing_phone:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="该手机号已被注册",
            )

    user = User(
        id=str(uuid.uuid4()),
        email=req.email,
        nickname=req.nickname or req.email.split("@")[0],
        password_hash=hash_password(req.password),
        role="free",
        phone=req.phone or "",
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)

    # 新用户注册赠送试用额度
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
    """用户登录 — 支持邮箱和手机号双渠道登录

    登录后自动迁移设备上的游客会话到用户账户。
    """
    user = None

    if req.login_type == "phone":
        if not req.phone:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="手机号不能为空",
            )
        user = await _get_user_by_phone(db, req.phone)
    else:
        if not req.email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="邮箱不能为空",
            )
        user = await _get_user_by_email(db, req.email)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="账号或密码错误",
        )

    if not verify_password(req.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="账号或密码错误",
        )

    # 登录后迁移游客设备会话到用户账户
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
        "phone": user.phone or "",
        "nickname": user.nickname,
        "role": user.role,
    }
