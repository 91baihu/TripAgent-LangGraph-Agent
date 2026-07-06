"""可视化管道 E2E 测试 — 验证工具解析到 SSE 事件到前端数据状态的完整链路"""

import pytest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))


class TestVisualizationPipeline:
    """验证工具返回 -> 解析 -> 结构化数据的完整链路"""

    def test_route_to_geo_data(self):
        """验证路线工具返回 -> 解析"""
        from tools.route import plan_route
        from tools.result_parser import parse_route_result

        route_text = plan_route.invoke(
            {"spot_a": "故宫", "spot_b": "颐和园", "city": "北京"}
        )
        parsed = parse_route_result(route_text)

        assert parsed["type"] == "route"
        assert parsed["distance_km"] > 0
        assert len(parsed["spots"]) == 2
        assert "polyline" in parsed
        for spot in parsed["spots"]:
            assert -90 <= spot["lat"] <= 90
            assert -180 <= spot["lng"] <= 180

    def test_restaurant_to_ranking_data(self):
        """验证餐厅工具返回 -> 解析 -> 排名数据"""
        from tools.restaurants import search_restaurants
        from tools.result_parser import parse_restaurant_result

        food_text = search_restaurants.invoke(
            {"city": "北京", "near_spot": "故宫", "budget_level": "中等"}
        )
        parsed = parse_restaurant_result(food_text)

        assert parsed["type"] == "restaurant_list"
        assert len(parsed["items"]) > 0
        for item in parsed["items"]:
            assert "rank" in item
            assert "name" in item
            assert "price_per_person" in item
            assert item["rank"] > 0

    def test_hotel_to_ranking_data(self):
        """验证酒店工具返回 -> 解析 -> 排名数据"""
        from tools.hotels import search_hotels
        from tools.result_parser import parse_hotel_result

        hotel_text = search_hotels.invoke(
            {"city": "北京", "budget_level": "高档"}
        )
        parsed = parse_hotel_result(hotel_text)

        assert parsed["type"] == "hotel_list"
        assert len(parsed["items"]) > 0
        for item in parsed["items"]:
            assert "rank" in item
            assert "name" in item
            assert "price_per_night" in item


class TestAgentServiceGeoEvents:
    """验证 _build_geo_event 对各类工具的处理"""

    def test_build_geo_event_route(self):
        from tools.route import plan_route
        from server.services.agent_service import _build_geo_event

        route_text = plan_route.invoke(
            {"spot_a": "故宫", "spot_b": "天坛", "city": "北京"}
        )
        event = _build_geo_event("plan_route", route_text)

        assert event is not None
        assert event.type == "geo_data"
        assert event.data["geo_type"] == "route"
        assert len(event.data["spots"]) == 2

    def test_build_geo_event_restaurant(self):
        from tools.restaurants import search_restaurants
        from server.services.agent_service import _build_geo_event

        food_text = search_restaurants.invoke(
            {"city": "北京", "near_spot": "故宫", "budget_level": "中等"}
        )
        event = _build_geo_event("search_restaurants", food_text)

        assert event is not None
        assert event.type == "geo_data"
        assert event.data["geo_type"] == "restaurant_ranking"
        assert len(event.data["items"]) > 0

    def test_build_geo_event_hotel(self):
        from tools.hotels import search_hotels
        from server.services.agent_service import _build_geo_event

        hotel_text = search_hotels.invoke(
            {"city": "北京", "budget_level": "高档"}
        )
        event = _build_geo_event("search_hotels", hotel_text)

        assert event is not None
        assert event.type == "geo_data"
        assert event.data["geo_type"] == "hotel_ranking"
        assert len(event.data["items"]) > 0

    def test_build_geo_event_unknown_tool(self):
        from server.services.agent_service import _build_geo_event

        event = _build_geo_event("get_weather", "晴 28度")
        assert event is None


class TestDesignConsistency:
    """设计一致性验证 — 解析器输出可用项目主色渲染"""

    def test_route_spots_have_valid_coords_for_map(self):
        from tools.result_parser import parse_route_result
        from tools.amap_service import FALLBACK_COORDS

        text = (
            "## 故宫 → 颐和园\n\n"
            "| 距离 | **21.8 km** |\n"
            "| 预计耗时 | **35 分钟** |\n"
            "| 推荐交通 | **打车/驾车** |"
        )
        result = parse_route_result(text)

        for spot in result["spots"]:
            assert spot["lat"] != 0.0
            assert spot["lng"] != 0.0
            if spot["name"] in FALLBACK_COORDS:
                expected_lat, expected_lng = FALLBACK_COORDS[spot["name"]]
                assert spot["lat"] == expected_lat
                assert spot["lng"] == expected_lng
