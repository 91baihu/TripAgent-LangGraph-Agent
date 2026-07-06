"""结果解析器单元测试"""

import pytest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))


# 测试用的 Markdown 文本
ROUTE_TEXT = (
    "## 故宫 → 颐和园\n\n"
    "| 项目 | 详情 |\n"
    "|------|------|\n"
    "| 距离 | **21.8 km** |\n"
    "| 预计耗时 | **35 分钟** |\n"
    "| 推荐交通 | **打车/驾车** |\n"
    "| 路线说明 | 距离较远，建议打车或驾车前往 |\n\n"
    "*数据来源： 📍本地估算*"
)

RESTAURANT_TEXT = (
    "## 北京 美食推荐\n\n"
    "*故宫 附近 · 中等预算 · 内置数据*\n\n"
    "1. **四季民福烤鸭店(故宫店)** | 北京菜 | 人均¥150 | 靠近故宫\n"
    "2. **铃木食堂(南锣鼓巷)** | 日料 | 人均¥80 | 靠近南锣鼓巷\n"
    "3. **小吊梨汤(望京)** | 北京菜 | 人均¥90 | 靠近798艺术区"
)

HOTEL_TEXT = (
    "## 北京 酒店推荐\n\n"
    "*故宫 附近 · 中等预算 · 内置数据*\n\n"
    "1. **北京饭店** | 五星级 | ¥800/晚\n"
    "   步行5分钟到故宫 | 1晚预估 ¥800\n\n"
    "2. **全季酒店(前门店)** | 经济型 | ¥280/晚\n"
    "   性价比高，交通便利 | 1晚预估 ¥280"
)


class TestParseRouteResult:
    """路线结果解析测试"""

    def test_parse_basic_route(self):
        from tools.result_parser import parse_route_result

        result = parse_route_result(ROUTE_TEXT)
        assert result["type"] == "route"
        assert result["distance_km"] == 21.8
        assert result["duration_min"] == 35
        assert result["transport"] == "打车/驾车"
        assert len(result["spots"]) == 2
        assert result["spots"][0]["name"] == "故宫"
        assert result["spots"][1]["name"] == "颐和园"
        assert "polyline" in result

    def test_parse_route_spots_have_coordinates(self):
        from tools.result_parser import parse_route_result

        result = parse_route_result(ROUTE_TEXT)
        for spot in result["spots"]:
            assert "lat" in spot
            assert "lng" in spot
            assert -90 <= spot["lat"] <= 90
            assert -180 <= spot["lng"] <= 180

    def test_parse_empty_text(self):
        from tools.result_parser import parse_route_result

        result = parse_route_result("")
        assert result["type"] == "route"
        assert result["spots"] == []

    def test_parse_short_walk(self):
        from tools.result_parser import parse_route_result

        text = (
            "## 景山公园 → 北海公园\n\n"
            "| 项目 | 详情 |\n"
            "| 距离 | **0.8 km** |\n"
            "| 预计耗时 | **10 分钟** |\n"
            "| 推荐交通 | **步行** |\n"
            "| 路线说明 | 距离很近 |"
        )
        result = parse_route_result(text)
        assert result["distance_km"] == 0.8
        assert result["transport"] == "步行"


class TestParseRestaurantResult:
    """餐厅结果解析测试"""

    def test_parse_mock_data(self):
        from tools.result_parser import parse_restaurant_result

        result = parse_restaurant_result(RESTAURANT_TEXT)
        assert result["type"] == "restaurant_list"
        assert result["city"] == "北京"
        assert result["near_spot"] == "故宫"
        assert len(result["items"]) == 3
        assert result["items"][0]["rank"] == 1
        assert result["items"][0]["price_per_person"] == 150
        assert result["items"][1]["price_per_person"] == 80
        assert "四季民福" in result["items"][0]["name"]

    def test_parse_items_have_coordinates(self):
        from tools.result_parser import parse_restaurant_result

        result = parse_restaurant_result(RESTAURANT_TEXT)
        for item in result["items"]:
            assert "lat" in item
            assert "lng" in item


class TestParseHotelResult:
    """酒店结果解析测试"""

    def test_parse_mock_data(self):
        from tools.result_parser import parse_hotel_result

        result = parse_hotel_result(HOTEL_TEXT)
        assert result["type"] == "hotel_list"
        assert len(result["items"]) == 2
        assert result["items"][0]["price_per_night"] == 800
        assert result["items"][1]["price_per_night"] == 280
        assert result["items"][0]["type"] == "五星级"

    def test_parse_items_have_coordinates(self):
        from tools.result_parser import parse_hotel_result

        result = parse_hotel_result(HOTEL_TEXT)
        for item in result["items"]:
            assert "lat" in item
            assert "lng" in item


class TestExtractFromTrace:
    """从 Streamlit trace 中提取数据测试"""

    def test_extract_route_spots(self):
        from tools.result_parser import extract_route_spots

        trace = [
            {
                "num": 1,
                "action": "🔧 调用工具",
                "tool": "plan_route",
                "input": {"spot_a": "故宫", "spot_b": "颐和园", "city": "北京"},
            },
            {
                "num": 2,
                "action": "🔧 调用工具",
                "tool": "plan_route",
                "input": {"spot_a": "颐和园", "spot_b": "天坛", "city": "北京"},
            },
        ]

        spots = extract_route_spots(trace)
        assert len(spots) == 3
        names = {s["name"] for s in spots}
        assert names == {"故宫", "颐和园", "天坛"}

    def test_extract_restaurant_items(self):
        from tools.result_parser import extract_restaurant_items

        trace = [
            {
                "num": 1,
                "action": "🔧 调用工具",
                "tool": "search_restaurants",
                "output": RESTAURANT_TEXT,
            },
        ]

        items = extract_restaurant_items(trace)
        assert len(items) == 3
        assert items[0]["name"] == "四季民福烤鸭店(故宫店)"

    def test_extract_empty_trace(self):
        from tools.result_parser import (
            extract_route_spots,
            extract_restaurant_items,
        )

        assert extract_route_spots([]) == []
        assert extract_restaurant_items([]) == []
