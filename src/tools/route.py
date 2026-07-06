"""路线规划工具 — 高德地图 API + 本地 fallback"""

from langchain_core.tools import tool

from .amap_service import amap_service


@tool
def plan_route(spot_a: str, spot_b: str, city: str = "北京") -> str:
    """计算两个景点之间的距离和推荐交通方式。安排每日行程顺序时使用。

    优先使用高德地图 API 获取真实路线数据；API 不可用时自动降级为本地坐标计算。

    Args:
        spot_a: 起点景点名称
        spot_b: 终点景点名称
        city: 所在城市，默认"北京"
    """
    result = amap_service.plan_route(spot_a, spot_b, city=city)

    if result.distance_km == 0 and result.duration_min == 0:
        return result.route_detail

    source_tag = " 🛰️高德地图" if result.source == "amap_api" else " 📍本地估算"
    return (
        f"## {spot_a} → {spot_b}\n\n"
        f"| 项目 | 详情 |\n"
        f"|------|------|\n"
        f"| 距离 | **{result.distance_km:.1f} km** |\n"
        f"| 预计耗时 | **{result.duration_min} 分钟** |\n"
        f"| 推荐交通 | **{result.transport}** |\n"
        f"| 路线说明 | {result.route_detail} |\n\n"
        f"*数据来源：{source_tag}*"
    )
