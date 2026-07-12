"""管理员路由 — 系统管理、用户管理、数据统计

管理员拥有全部功能权限：
- 无限额度（不受套餐限制）
- 查看/管理所有用户
- 查看所有订单和会话
- 系统统计数据
- 提升/降级用户角色
"""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import select, func, text
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_db
from ..auth import get_current_user, require_role
from ..models import User, Trip, ChatSession, PurchaseOrder, CreditTransaction, DeviceSession
from ..services.credit_service import credit_service

router = APIRouter(prefix="/admin", tags=["管理员"])


# ========== 请求模型 ==========
class PromoteRequest(BaseModel):
    user_id: str
    role: str = Field(..., pattern="^(free|pro|family|admin)$")


class GrantCreditsRequest(BaseModel):
    user_id: str
    amount: int = Field(..., gt=0, le=100000)
    description: str = Field(default="管理员赠送", max_length=200)


class UpdateUserRequest(BaseModel):
    nickname: Optional[str] = Field(None, max_length=100)
    is_active: Optional[bool] = None


# ========== 权限守卫 ==========
admin_required = require_role("admin")


# ========== 仪表盘统计 ==========
@router.get("/stats")
async def get_dashboard_stats(
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(admin_required),
):
    """获取系统仪表盘统计数据"""
    # 用户总数
    total_users = (await db.execute(select(func.count(User.id)))).scalar() or 0

    # 付费用户（pro + family）
    paid_users = (
        await db.execute(
            select(func.count(User.id)).where(User.role.in_(["pro", "family"]))
        )
    ).scalar() or 0

    # 管理员数
    admin_count = (
        await db.execute(select(func.count(User.id)).where(User.role == "admin"))
    ).scalar() or 0

    # 行程总数
    total_trips = (await db.execute(select(func.count(Trip.id)))).scalar() or 0

    # 会话总数
    total_sessions = (
        await db.execute(select(func.count(ChatSession.id)))
    ).scalar() or 0

    # 订单统计
    total_orders = (
        await db.execute(select(func.count(PurchaseOrder.id)))
    ).scalar() or 0
    paid_orders = (
        await db.execute(
            select(func.count(PurchaseOrder.id)).where(
                PurchaseOrder.status == "paid"
            )
        )
    ).scalar() or 0

    # 总收入（分）
    total_revenue_cents = (
        await db.execute(
            select(func.coalesce(func.sum(PurchaseOrder.amount_cents), 0)).where(
                PurchaseOrder.status == "paid"
            )
        )
    ).scalar() or 0

    # 游客设备数
    total_devices = (
        await db.execute(select(func.count(DeviceSession.id)))
    ).scalar() or 0

    # 今日注册
    from datetime import datetime, timezone
    today = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    today_users = (
        await db.execute(
            select(func.count(User.id)).where(User.created_at >= today)
        )
    ).scalar() or 0

    return {
        "users": {
            "total": total_users,
            "paid": paid_users,
            "admin": admin_count,
            "today_new": today_users,
        },
        "content": {
            "total_trips": total_trips,
            "total_sessions": total_sessions,
        },
        "revenue": {
            "total_orders": total_orders,
            "paid_orders": paid_orders,
            "total_revenue_cents": total_revenue_cents,
            "total_revenue_display": f"¥{total_revenue_cents / 100:.2f}",
        },
        "devices": total_devices,
    }


# ========== 用户管理 ==========
@router.get("/users")
async def list_users(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    role: Optional[str] = Query(None, pattern="^(free|pro|family|admin)$"),
    search: Optional[str] = Query(None, max_length=100),
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(admin_required),
):
    """管理员查看所有用户列表"""
    query = select(User)

    if role:
        query = query.where(User.role == role)
    if search:
        query = query.where(
            (User.email.ilike(f"%{search}%"))
            | (User.nickname.ilike(f"%{search}%"))
        )

    # 总数
    count_query = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_query)).scalar() or 0

    # 分页
    query = query.order_by(User.created_at.desc()).offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    users = result.scalars().all()

    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "items": [
            {
                "id": u.id,
                "email": u.email,
                "nickname": u.nickname,
                "role": u.role,
                "is_active": u.is_active,
                "credits_balance": u.credits_balance,
                "monthly_quota": u.monthly_quota,
                "created_at": u.created_at.isoformat() if u.created_at else None,
            }
            for u in users
        ],
    }


@router.get("/users/{user_id}")
async def get_user_detail(
    user_id: str,
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(admin_required),
):
    """管理员查看用户详情"""
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")

    # 统计用户数据
    trip_count = (
        await db.execute(
            select(func.count(Trip.id)).where(Trip.user_id == user_id)
        )
    ).scalar() or 0
    session_count = (
        await db.execute(
            select(func.count(ChatSession.id)).where(ChatSession.user_id == user_id)
        )
    ).scalar() or 0
    order_count = (
        await db.execute(
            select(func.count(PurchaseOrder.id)).where(PurchaseOrder.user_id == user_id)
        )
    ).scalar() or 0

    return {
        "id": user.id,
        "email": user.email,
        "nickname": user.nickname,
        "role": user.role,
        "is_active": user.is_active,
        "credits_balance": user.credits_balance,
        "monthly_quota": user.monthly_quota,
        "quota_reset_at": user.quota_reset_at.isoformat() if user.quota_reset_at else None,
        "created_at": user.created_at.isoformat() if user.created_at else None,
        "updated_at": user.updated_at.isoformat() if user.updated_at else None,
        "stats": {
            "trip_count": trip_count,
            "session_count": session_count,
            "order_count": order_count,
        },
    }


@router.patch("/users/{user_id}")
async def update_user(
    user_id: str,
    body: UpdateUserRequest,
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(admin_required),
):
    """管理员编辑用户信息"""
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")

    if body.nickname is not None:
        user.nickname = body.nickname
    if body.is_active is not None:
        user.is_active = body.is_active

    await db.commit()
    return {"status": "ok", "message": "用户信息已更新"}


@router.post("/users/{user_id}/promote")
async def promote_user(
    user_id: str,
    body: PromoteRequest,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(admin_required),
):
    """管理员提升/修改用户角色"""
    if user_id == current_user["sub"]:
        raise HTTPException(status_code=400, detail="不能修改自己的角色")

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")

    old_role = user.role
    user.role = body.role

    # 如果提升为 admin，给予无限额度标识
    if body.role == "admin":
        user.credits_balance = 999999
        user.monthly_quota = 999999

    await db.commit()

    return {
        "status": "ok",
        "message": f"用户 {user.email} 角色已从 {old_role} 变更为 {body.role}",
        "user_id": user_id,
        "old_role": old_role,
        "new_role": body.role,
    }


@router.post("/users/{user_id}/grant-credits")
async def admin_grant_credits(
    user_id: str,
    body: GrantCreditsRequest,
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(admin_required),
):
    """管理员手动赠送额度"""
    from ..services.billing_service import billing_service

    try:
        result = await billing_service.grant_credits(
            db,
            user_id=user_id,
            amount=body.amount,
            description=body.description,
        )
        await db.commit()
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# ========== 会话管理 ==========
@router.get("/sessions")
async def list_all_sessions(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(admin_required),
):
    """管理员查看所有会话"""
    query = select(ChatSession).order_by(ChatSession.created_at.desc())
    count_query = select(func.count(ChatSession.id))
    total = (await db.execute(count_query)).scalar() or 0

    query = query.offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    sessions = result.scalars().all()

    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "items": [
            {
                "id": s.id,
                "user_id": s.user_id,
                "title": s.title,
                "city": s.city,
                "status": s.status,
                "created_at": s.created_at.isoformat() if s.created_at else None,
                "updated_at": s.updated_at.isoformat() if s.updated_at else None,
            }
            for s in sessions
        ],
    }


# ========== 行程管理 ==========
@router.get("/trips")
async def list_all_trips(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(admin_required),
):
    """管理员查看所有行程"""
    query = select(Trip).order_by(Trip.created_at.desc())
    count_query = select(func.count(Trip.id))
    total = (await db.execute(count_query)).scalar() or 0

    query = query.offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    trips = result.scalars().all()

    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "items": [
            {
                "id": t.id,
                "user_id": t.user_id,
                "title": t.title,
                "city": t.city,
                "days": t.days,
                "status": t.status,
                "created_at": t.created_at.isoformat() if t.created_at else None,
            }
            for t in trips
        ],
    }


# ========== 快速提升当前用户为管理员（开发用） ==========
@router.post("/self-promote")
async def self_promote_to_admin(
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """开发/测试用：将当前登录用户提升为管理员

    仅在 APP_ENV=dev 时可用。
    """
    import os
    if os.getenv("APP_ENV", "dev") not in ("dev", "development", "test"):
        raise HTTPException(status_code=403, detail="仅开发环境可用")

    result = await db.execute(select(User).where(User.id == current_user["sub"]))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")

    user.role = "admin"
    user.credits_balance = 999999
    user.monthly_quota = 999999
    await db.commit()

    return {
        "status": "ok",
        "message": f"用户 {user.email} 已提升为管理员，享有无限额度",
        "user_id": user.id,
        "role": "admin",
        "credits_balance": 999999,
    }
