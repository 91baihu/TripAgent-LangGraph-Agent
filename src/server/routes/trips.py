"""行程 CRUD 路由"""

import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, Query

from ..schemas.trip import (
    TripCreate,
    TripUpdate,
    TripResponse,
    TripListResponse,
)

router = APIRouter()

# ========== 临时内存存储（后续替换为 PostgreSQL） ==========
_trips_db: dict = {}
_share_tokens: set = set()


def _generate_share_token() -> str:
    """生成唯一分享 token"""
    while True:
        token = str(uuid.uuid4())[:12]
        if token not in _share_tokens:
            _share_tokens.add(token)
            return token


@router.post("/trips", response_model=TripResponse, status_code=201)
async def create_trip(trip: TripCreate):
    """创建新行程"""
    trip_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc)

    trip_data = {
        "id": trip_id,
        "title": trip.title,
        "city": trip.city,
        "days": trip.days,
        "itinerary_json": trip.itinerary_json,
        "status": "draft",
        "share_token": None,
        "created_at": now,
        "updated_at": now,
    }

    _trips_db[trip_id] = trip_data
    return TripResponse(**trip_data)


@router.get("/trips", response_model=TripListResponse)
async def list_trips(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=10, ge=1, le=50),
):
    """获取行程列表"""
    all_trips = list(_trips_db.values())
    all_trips.sort(key=lambda t: t["updated_at"], reverse=True)

    total = len(all_trips)
    start = (page - 1) * page_size
    end = start + page_size
    page_trips = all_trips[start:end]

    return TripListResponse(
        trips=[TripResponse(**t) for t in page_trips],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/trips/{trip_id}", response_model=TripResponse)
async def get_trip(trip_id: str):
    """获取单个行程详情"""
    trip = _trips_db.get(trip_id)
    if not trip:
        raise HTTPException(status_code=404, detail="行程不存在")
    return TripResponse(**trip)


@router.patch("/trips/{trip_id}", response_model=TripResponse)
async def update_trip(trip_id: str, update: TripUpdate):
    """更新行程"""
    trip = _trips_db.get(trip_id)
    if not trip:
        raise HTTPException(status_code=404, detail="行程不存在")

    update_data = update.model_dump(exclude_unset=True)
    trip.update(update_data)
    trip["updated_at"] = datetime.now(timezone.utc)

    return TripResponse(**trip)


@router.delete("/trips/{trip_id}", status_code=204)
async def delete_trip(trip_id: str):
    """删除行程"""
    if trip_id not in _trips_db:
        raise HTTPException(status_code=404, detail="行程不存在")
    del _trips_db[trip_id]


@router.post("/trips/{trip_id}/share")
async def share_trip(trip_id: str):
    """生成分享链接"""
    trip = _trips_db.get(trip_id)
    if not trip:
        raise HTTPException(status_code=404, detail="行程不存在")

    token = _generate_share_token()
    trip["share_token"] = token
    trip["updated_at"] = datetime.now(timezone.utc)

    return {"share_token": token, "share_url": f"/share/{token}"}


@router.get("/share/{token}", response_model=TripResponse)
async def get_shared_trip(token: str):
    """通过分享 token 获取行程"""
    for trip in _trips_db.values():
        if trip.get("share_token") == token:
            return TripResponse(**trip)
    raise HTTPException(status_code=404, detail="分享链接已失效或不存在")
