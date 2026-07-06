"""工具调试路由 — 单独测试每个工具"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from ...tools.attractions import search_attractions
from ...tools.weather import get_weather
from ...tools.route import plan_route
from ...tools.restaurants import search_restaurants

router = APIRouter()


class ToolTestRequest(BaseModel):
    """工具测试请求"""
    params: dict = Field(default_factory=dict, description="工具参数字典")


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
    """测试路线规划工具"""
    try:
        result = plan_route.invoke(req.params)
        return {"tool": "plan_route", "result": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/tools/search_restaurants")
async def tool_search_restaurants(req: ToolTestRequest):
    """测试美食搜索工具"""
    try:
        result = search_restaurants.invoke(req.params)
        return {"tool": "search_restaurants", "result": result}
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
                "description": "计算两个景点之间的距离和推荐交通方式",
                "params": {"spot_a": "string (required)", "spot_b": "string (required)"},
            },
            {
                "name": "search_restaurants",
                "description": "搜索指定城市的美食推荐",
                "params": {
                    "city": "string (required)",
                    "near_spot": "string (optional)",
                    "budget_level": "string (optional: 经济/中等/高档)",
                },
            },
        ]
    }
