"""行程相关 Pydantic 模型"""

from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, Field


class TripCreate(BaseModel):
    """创建行程"""
    title: str = Field(..., min_length=1, max_length=100, examples=["北京3日亲子游"])
    city: str = Field(..., min_length=1, max_length=50, examples=["北京"])
    days: int = Field(default=3, ge=1, le=30)
    itinerary_json: dict = Field(default_factory=dict)

    class Config:
        json_schema_extra = {
            "example": {
                "title": "北京3日亲子游",
                "city": "北京",
                "days": 3,
                "itinerary_json": {
                    "day1": [
                        {"name": "故宫", "time": "09:00-12:00", "price": 60},
                        {"name": "景山公园", "time": "13:00-15:00", "price": 2},
                    ]
                },
            }
        }


class TripUpdate(BaseModel):
    """更新行程"""
    title: Optional[str] = None
    itinerary_json: Optional[dict] = None
    status: Optional[str] = Field(default=None, pattern="^(draft|confirmed|completed|archived)$")


class TripResponse(BaseModel):
    """行程响应"""
    id: str
    title: str
    city: str
    days: int
    itinerary_json: dict
    status: str
    share_token: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class TripListResponse(BaseModel):
    """行程列表响应"""
    trips: List[TripResponse]
    total: int
    page: int
    page_size: int
