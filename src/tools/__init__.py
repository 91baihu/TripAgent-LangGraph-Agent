"""TripAgent 工具集 — 5 个旅行规划工具 + 结果解析器"""

from .attractions import search_attractions
from .weather import get_weather
from .route import plan_route
from .restaurants import search_restaurants
from .hotels import search_hotels
from .amap_service import amap_service
from .result_parser import (
    parse_route_result,
    parse_restaurant_result,
    parse_hotel_result,
    extract_route_spots,
    extract_restaurant_items,
    extract_hotel_items,
)

__all__ = [
    "search_attractions",
    "get_weather",
    "plan_route",
    "search_restaurants",
    "search_hotels",
    "amap_service",
    "parse_route_result",
    "parse_restaurant_result",
    "parse_hotel_result",
    "extract_route_spots",
    "extract_restaurant_items",
    "extract_hotel_items",
]
