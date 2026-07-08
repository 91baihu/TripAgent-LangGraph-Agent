"""路线规划工具 — 高德地图 API + 本地 fallback + 缓存"""

from langchain_core.tools import tool

from .amap_service import amap_service

# 兼容不同导入路径
try:
    from ..server.cache import cache_service
except ImportError:
    try:
        from server.cache import cache_service
    except ImportError:
        cache_service = None


@tool
def plan_route(spot_a: str, spot_b: str, city: str = "北京") -> str:
    """计算两个景点之间的距离和推荐交通方式。安排每日行程顺序时使用。

    优先使用高德地图 API 获取真实路线数据；API 不可用时自动降级为本地坐标计算。

    Args:
        spot_a: 起点景点名称
        spot_b: 终点景点名称
        city: 所在城市，默认"北京"
    """
    # 检查缓存（路线 30 分钟内不重复请求）
    cache_args = {"spot_a": spot_a, "spot_b": spot_b, "city": city}
    if cache_service:
        cached = cache_service.get_tool_result_sync("plan_route", cache_args)
        if cached:
            return cached

    result = amap_service.plan_route(spot_a, spot_b, city=city)

    if result.distance_km == 0 and result.duration_min == 0:
        output = result.route_detail
    else:
        source_tag = " 🛰️高德地图" if result.source == "amap_api" else " 📍本地估算"
        output = (
            f"## {spot_a} → {spot_b}\n\n"
            f"| 项目 | 详情 |\n"
            f"|------|------|\n"
            f"| 距离 | **{result.distance_km:.1f} km** |\n"
            f"| 预计耗时 | **{result.duration_min} 分钟** |\n"
            f"| 推荐交通 | **{result.transport}** |\n"
            f"| 路线说明 | {result.route_detail} |\n\n"
            f"*数据来源：{source_tag}*"
        )

    # 写入缓存（30 分钟 TTL）
    if cache_service:
        cache_service.set_tool_result_sync("plan_route", cache_args, output, ttl=1800)

    return output
