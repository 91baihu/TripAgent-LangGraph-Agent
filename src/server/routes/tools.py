"""工具调试路由 — 单独测试每个工具 & Token 用量查询"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

try:
    from ...tools.attractions import search_attractions
    from ...tools.weather import get_weather
    from ...tools.route import plan_route
    from ...tools.restaurants import search_restaurants
    from ...tools.hotels import search_hotels
except ImportError:
    from tools.attractions import search_attractions
    from tools.weather import get_weather
    from tools.route import plan_route
    from tools.restaurants import search_restaurants
    from tools.hotels import search_hotels

try:
    from ..token_tracker import token_tracker
except ImportError:
    token_tracker = None

router = APIRouter()


class ToolTestRequest(BaseModel):
    """工具测试请求"""
    params: dict = Field(default_factory=dict, description="工具参数字典")


# ========== 工具测试 ==========

@router.post("/tools/search_attractions")
async def tool_search_attractions(req: ToolTestRequest):
    """测试景点搜索工具"""
    try:
        result = search_attractions.invoke(req.params)
        return {"tool": "search_attractions", "result": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/tools/get_weather")
async def tool_get_weather(req: ToolTestRequest):
    """测试天气查询工具"""
    try:
        result = get_weather.invoke(req.params)
        return {"tool": "get_weather", "result": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/tools/plan_route")
async def tool_plan_route(req: ToolTestRequest):
    """测试路线规划工具（支持高德地图 API）"""
    try:
        result = plan_route.invoke(req.params)
        return {"tool": "plan_route", "result": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/tools/search_restaurants")
async def tool_search_restaurants(req: ToolTestRequest):
    """测试美食搜索工具（支持高德 POI 搜索）"""
    try:
        result = search_restaurants.invoke(req.params)
        return {"tool": "search_restaurants", "result": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/tools/search_hotels")
async def tool_search_hotels(req: ToolTestRequest):
    """测试酒店搜索工具（支持高德 POI 搜索）"""
    try:
        result = search_hotels.invoke(req.params)
        return {"tool": "search_hotels", "result": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/tools")
async def list_tools():
    """列出所有可用工具及参数"""
    return {
        "tools": [
            {
                "name": "search_attractions",
                "description": "搜索指定城市的景点信息",
                "params": {"city": "string (required)", "keyword": "string (optional)"},
            },
            {
                "name": "get_weather",
                "description": "查询指定城市和日期的天气",
                "params": {"city": "string (required)", "date": "string (optional)"},
            },
            {
                "name": "plan_route",
                "description": "计算两个景点之间的距离和推荐交通方式（高德地图+本地计算）",
                "params": {"spot_a": "string (required)", "spot_b": "string (required)", "city": "string (optional)"},
            },
            {
                "name": "search_restaurants",
                "description": "搜索指定城市的美食推荐（高德POI+内置数据）",
                "params": {
                    "city": "string (required)",
                    "near_spot": "string (optional)",
                    "budget_level": "string (optional: 经济/中等/高档)",
                },
            },
            {
                "name": "search_hotels",
                "description": "搜索指定城市的酒店住宿（高德POI+内置数据）",
                "params": {
                    "city": "string (required)",
                    "near_spot": "string (optional)",
                    "budget_level": "string (optional: 经济/中等/高档/豪华)",
                    "check_in": "string (optional: 2026-07-10)",
                    "check_out": "string (optional: 2026-07-12)",
                },
            },
        ],
        "amap_api_available": (
            __import__("tools.amap_service", fromlist=["amap_service"]).amap_service.available
            if __import__("importlib").util.find_spec("tools.amap_service")
            else False
        ),
    }


# ========== Token 用量查询 ==========

@router.get("/usage")
async def get_usage(session_id: str = ""):
    """查询 Token 用量和成本（如果 token_tracker 可用）"""
    if token_tracker is None:
        return {"error": "Token Tracker 未初始化"}

    if session_id:
        summary = token_tracker.get_summary(session_id=session_id)
    else:
        summary = token_tracker.get_summary()

    return {
        "summary": summary,
        "alert_threshold_yuan": token_tracker.alert_threshold,
        "is_over_budget": token_tracker.is_over_budget(),
    }


@router.get("/usage/report")
async def get_usage_report(session_id: str = ""):
    """获取人类可读的 Token 用量报告"""
    if token_tracker is None:
        return {"report": "Token Tracker 未初始化"}

    return {"report": token_tracker.format_cost_report(session_id=session_id)}
