"""行程 CRUD 路由 (PostgreSQL)"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from ..auth import get_current_user
from ..database import get_db
from ..models import Trip
from ..schemas.trip import (
    TripCreate,
    TripUpdate,
    TripResponse,
    TripListResponse,
)

router = APIRouter()


# ========== 辅助函数 ==========
def _trip_to_response(trip: Trip) -> TripResponse:
    """将 ORM 模型转换为 Pydantic 响应"""
    return TripResponse(
        id=trip.id,
        title=trip.title,
        city=trip.city,
        days=trip.days,
        itinerary_json=trip.itinerary_json,
        status=trip.status,
        share_token=trip.share_token,
        created_at=trip.created_at,
        updated_at=trip.updated_at,
    )


async def _get_trip_or_404(db: AsyncSession, trip_id: str, user_id: str | None = None) -> Trip:
    """查询行程，不存在或无权访问时抛出 404"""
    stmt = select(Trip).where(Trip.id == trip_id)
    if user_id:
        stmt = stmt.where(Trip.user_id == user_id)
    result = await db.execute(stmt)
    trip = result.scalar_one_or_none()
    if not trip:
        raise HTTPException(status_code=404, detail="行程不存在")
    return trip


def _generate_share_token() -> str:
    """生成唯一分享 token"""
    return str(uuid.uuid4())[:12]


# ========== 路由 ==========
@router.post("/trips", response_model=TripResponse, status_code=201)
async def create_trip(
    trip_in: TripCreate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """创建新行程"""
    trip = Trip(
        id=str(uuid.uuid4()),
        user_id=current_user["sub"],
        title=trip_in.title,
        city=trip_in.city,
        days=trip_in.days,
        itinerary_json=trip_in.itinerary_json,
        status="draft",
    )
    db.add(trip)
    await db.commit()
    await db.refresh(trip)

    return _trip_to_response(trip)


@router.get("/trips", response_model=TripListResponse)
async def list_trips(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=10, ge=1, le=50),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """获取当前用户的行程列表"""
    user_id = current_user["sub"]

    # 查询总数
    count_stmt = select(func.count()).select_from(Trip).where(Trip.user_id == user_id)
    total_result = await db.execute(count_stmt)
    total = total_result.scalar() or 0

    # 分页查询
    stmt = (
        select(Trip)
        .where(Trip.user_id == user_id)
        .order_by(Trip.updated_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    result = await db.execute(stmt)
    trips = result.scalars().all()

    return TripListResponse(
        trips=[_trip_to_response(t) for t in trips],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/trips/{trip_id}", response_model=TripResponse)
async def get_trip(
    trip_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """获取单个行程详情"""
    trip = await _get_trip_or_404(db, trip_id, user_id=current_user["sub"])
    return _trip_to_response(trip)


@router.patch("/trips/{trip_id}", response_model=TripResponse)
async def update_trip(
    trip_id: str,
    update: TripUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """更新行程"""
    trip = await _get_trip_or_404(db, trip_id, user_id=current_user["sub"])

    update_data = update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(trip, key, value)

    await db.commit()
    await db.refresh(trip)

    return _trip_to_response(trip)


@router.delete("/trips/{trip_id}", status_code=204)
async def delete_trip(
    trip_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """删除行程"""
    trip = await _get_trip_or_404(db, trip_id, user_id=current_user["sub"])
    await db.delete(trip)
    await db.commit()


@router.post("/trips/{trip_id}/share")
async def share_trip(
    trip_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """生成分享链接"""
    trip = await _get_trip_or_404(db, trip_id, user_id=current_user["sub"])

    # 生成唯一 token（冲突时重试）
    for _ in range(5):
        token = _generate_share_token()
        existing = await db.execute(
            select(Trip).where(Trip.share_token == token)
        )
        if not existing.scalar_one_or_none():
            break
    else:
        token = str(uuid.uuid4())  # fallback: 完整 UUID

    trip.share_token = token
    trip.share_expires_at = None  # 永不过期（可后续配置）
    await db.commit()

    return {"share_token": token, "share_url": f"/share/{token}"}


@router.get("/share/{token}", response_model=TripResponse)
async def get_shared_trip(
    token: str,
    db: AsyncSession = Depends(get_db),
):
    """通过分享 token 获取行程（无需登录）"""
    result = await db.execute(select(Trip).where(Trip.share_token == token))
    trip = result.scalar_one_or_none()

    if not trip:
        raise HTTPException(status_code=404, detail="分享链接已失效或不存在")

    return _trip_to_response(trip)
