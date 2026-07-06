"""路线规划工具 — 计算景点间距离和推荐交通方式"""

from langchain_core.tools import tool
import math

# 模拟城市坐标（后续可接高德/百度地图API）
CITY_COORDS = {
    "故宫": (39.9163, 116.3972),
    "故宫博物院": (39.9163, 116.3972),
    "颐和园": (39.9999, 116.2755),
    "中国科技馆": (39.9747, 116.3933),
    "北京动物园": (39.9423, 116.3364),
    "798艺术区": (39.9842, 116.4951),
    "景山公园": (39.9253, 116.3967),
    "南锣鼓巷": (39.9380, 116.4038),
    "天坛": (39.8822, 116.4066),
    "奥林匹克森林公园": (40.0207, 116.3924),
    "西湖": (30.2405, 120.1432),
    "灵隐寺": (30.2427, 120.1013),
    "杭州乐园": (30.2284, 120.2485),
}


@tool
def plan_route(spot_a: str, spot_b: str) -> str:
    """计算两个景点之间的距离和推荐交通方式。安排每日行程顺序时使用。

    Args:
        spot_a: 起点景点名称
        spot_b: 终点景点名称
    """
    coord_a = CITY_COORDS.get(spot_a)
    coord_b = CITY_COORDS.get(spot_b)

    if not coord_a or not coord_b:
        return f"未找到 '{spot_a}' 或 '{spot_b}' 的坐标信息"

    # 简化的距离计算（Haversine 公式的近似）
    lat_diff = (coord_b[0] - coord_a[0]) * 111
    lng_diff = (coord_b[1] - coord_a[1]) * 111 * math.cos(math.radians(coord_a[0]))
    distance_km = math.sqrt(lat_diff**2 + lng_diff**2)

    if distance_km < 3:
        transport = "步行约15分钟"
    elif distance_km < 10:
        transport = f"地铁约{distance_km * 2:.0f}分钟"
    else:
        transport = f"打车约{distance_km * 1.5:.0f}分钟"

    return f"{spot_a} → {spot_b}：直线距离约{distance_km:.1f}km，建议{transport}"
