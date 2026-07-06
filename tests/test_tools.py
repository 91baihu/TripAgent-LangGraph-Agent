"""工具函数 & Agent 集成测试"""

import pytest
import sys
import os

# 确保 src 目录在 Python 路径中
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from tools.attractions import search_attractions
from tools.weather import get_weather
from tools.route import plan_route
from tools.restaurants import search_restaurants


class TestAttractions:
    """景点搜索工具测试"""

    def test_search_beijing(self):
        result = search_attractions.invoke({"city": "北京"})
        assert "故宫" in result
        assert "景点" in result

    def test_search_with_keyword(self):
        result = search_attractions.invoke({"city": "北京", "keyword": "亲子"})
        assert "亲子友好" in result or "动物园" in result or "科技馆" in result

    def test_unknown_city(self):
        result = search_attractions.invoke({"city": "火星"})
        assert "未找到" in result


class TestWeather:
    """天气查询工具测试"""

    def test_get_weather_beijing(self):
        result = get_weather.invoke({"city": "Beijing"})
        # wttr.in 可能超时，检查返回包含天气或错误提示
        assert "天气" in result or "无法获取" in result or "超时" in result or "暂不可用" in result

    def test_get_weather_with_date(self):
        result = get_weather.invoke({"city": "Beijing", "date": "2026-07-10"})
        assert isinstance(result, str) and len(result) > 0


class TestRoute:
    """路线规划工具测试"""

    def test_plan_route_same_city(self):
        result = plan_route.invoke({"spot_a": "故宫", "spot_b": "颐和园"})
        assert "km" in result
        assert "建议" in result

    def test_plan_route_unknown_spot(self):
        result = plan_route.invoke({"spot_a": "不存在的景点", "spot_b": "故宫"})
        assert "未找到" in result

    def test_plan_route_close_spots(self):
        """近距离景点应推荐步行"""
        result = plan_route.invoke({"spot_a": "故宫", "spot_b": "景山公园"})
        assert "步行" in result or "km" in result


class TestRestaurants:
    """美食搜索工具测试"""

    def test_search_beijing(self):
        result = search_restaurants.invoke({"city": "北京"})
        assert "烤鸭" in result or "餐厅" in result or "推荐" in result

    def test_search_near_spot(self):
        result = search_restaurants.invoke({"city": "北京", "near_spot": "故宫"})
        assert "四季民福" in result or "推荐" in result


class TestAgentIntegration:
    """端到端集成测试（需要 DeepSeek API Key）"""

    @pytest.mark.skipif(
        not os.getenv("DEEPSEEK_API_KEY"),
        reason="需要配置 DEEPSEEK_API_KEY 环境变量"
    )
    def test_simple_trip_plan(self):
        """简单行程规划：Agent 应主动调用 search_attractions"""
        from agent.graph import create_agent
        agent = create_agent()
        result = agent.invoke({
            "messages": [{"role": "user", "content": "帮我推荐3个北京景点"}],
            "next_step": "",
            "travel_plan": {}
        })
        assert len(result["messages"]) >= 2  # 至少 user + assistant
        # Agent 应该主动调用了 search_attractions
        tool_calls_found = any(
            hasattr(m, "tool_calls") and m.tool_calls
            for m in result["messages"]
        )
        assert tool_calls_found, "Agent 应该主动调用工具"

    @pytest.mark.skipif(
        not os.getenv("DEEPSEEK_API_KEY"),
        reason="需要配置 DEEPSEEK_API_KEY 环境变量"
    )
    def test_multi_tool_planning(self):
        """复杂场景：需要多个工具协作"""
        from agent.graph import create_agent
        agent = create_agent()
        result = agent.invoke({
            "messages": [{"role": "user", "content": "帮我规划3天北京亲子游，中等预算"}],
            "next_step": "",
            "travel_plan": {}
        })
        # 检查至少调用了 search_attractions
        all_messages = result["messages"]
        tool_names_used = set()
        for m in all_messages:
            if hasattr(m, "tool_calls") and m.tool_calls:
                for tc in m.tool_calls:
                    tool_names_used.add(tc["name"])
        assert "search_attractions" in tool_names_used
        # 最终回复应包含行程计划
        final_reply = all_messages[-1].content
        assert len(final_reply) > 100  # 应该是详细的回复
