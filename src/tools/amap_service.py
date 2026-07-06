"""高德地图 API 服务 — 真实路线规划 + POI 搜索

提供：
- 地理编码（地名 → 坐标）
- 距离计算
- 路线规划（步行/驾车/公交）
- POI 搜索（餐厅、酒店等周边搜索）

文档：https://lbs.amap.com/api/webservice/summary/
"""

import os
import math
import hashlib
from typing import Optional, List, Dict, Tuple
from dataclasses import dataclass

import requests
from dotenv import load_dotenv

load_dotenv()

# ========== 配置 ==========
AMAP_API_KEY = os.getenv("AMAP_API_KEY", "")
AMAP_BASE = "https://restapi.amap.com/v3"

# 硬编码坐标（当 API 不可用时的 fallback）
FALLBACK_COORDS = {
    "故宫": (39.9163, 116.3972),
    "故宫博物院": (39.9163, 116.3972),
    "颐和园": (39.9999, 116.2755),
    "中国科技馆": (39.9747, 116.3933),
    "北京动物园": (39.9423, 116.3364),
    "798艺术区": (39.9842, 116.4951),
    "景山公园": (39.9253, 116.3967),
    "南锣鼓巷": (39.9380, 116.4038),
    "天坛": (39.8822, 116.4066),
    "天安门广场": (39.9054, 116.3976),
    "奥林匹克森林公园": (40.0207, 116.3924),
    "鸟巢": (39.9929, 116.3888),
    "水立方": (39.9913, 116.3899),
    "北海公园": (39.9242, 116.3957),
    "雍和宫": (39.9474, 116.4173),
    "八达岭长城": (40.3597, 116.0204),
    "西湖": (30.2405, 120.1432),
    "灵隐寺": (30.2427, 120.1013),
    "杭州乐园": (30.2284, 120.2485),
    "雷峰塔": (30.2312, 120.1482),
    "断桥残雪": (30.2582, 120.1495),
    "苏堤": (30.2435, 120.1389),
    "西溪湿地": (30.2693, 120.0607),
    "宋城": (30.1703, 120.0926),
}


@dataclass
class RouteResult:
    """路线规划结果"""
    distance_km: float           # 距离（公里）
    duration_min: int            # 预计耗时（分钟）
    transport: str               # 推荐交通方式
    route_detail: str            # 路线描述
    source: str                  # 数据来源: "amap_api" | "fallback"


class AmapService:
    """高德地图 API 服务封装

    所有方法均有 fallback 机制：API 不可用时自动降级为本地计算。
    """

    def __init__(self, api_key: str = ""):
        self.api_key = api_key or AMAP_API_KEY
        self._available = None  # 延迟检测

    @property
    def available(self) -> bool:
        """检测 API 是否可用"""
        if self._available is None:
            self._available = bool(self.api_key) and len(self.api_key) > 10
        return self._available

    # ========== 地理编码 ==========

    def geocode(self, address: str, city: str = "北京") -> Optional[Tuple[float, float]]:
        """将地址转换为坐标（经纬度）

        Args:
            address: 地址/地名
            city: 所在城市

        Returns:
            (lat, lng) 或 None
        """
        # 先检查 fallback 缓存
        if address in FALLBACK_COORDS:
            return FALLBACK_COORDS[address]

        if not self.available:
            return self._fuzzy_geocode(address)

        try:
            resp = requests.get(
                f"{AMAP_BASE}/geocode/geo",
                params={
                    "key": self.api_key,
                    "address": address,
                    "city": city,
                },
                timeout=5,
            )
            data = resp.json()
            if data.get("status") == "1" and data.get("geocodes"):
                loc = data["geocodes"][0]["location"]
                lng, lat = loc.split(",")
                return (float(lat), float(lng))
        except Exception:
            pass

        return self._fuzzy_geocode(address)

    def _fuzzy_geocode(self, address: str) -> Optional[Tuple[float, float]]:
        """模糊查找坐标（从 fallback 字典中部分匹配）"""
        for name, coords in FALLBACK_COORDS.items():
            if name in address or address in name:
                return coords
        return None

    # ========== 距离计算 ==========

    def get_distance(
        self,
        origin: Tuple[float, float],
        destination: Tuple[float, float],
    ) -> Tuple[float, int]:
        """计算两点间驾车距离和耗时

        Returns:
            (distance_km, duration_min)
        """
        if self.available:
            try:
                resp = requests.get(
                    f"{AMAP_BASE}/distance",
                    params={
                        "key": self.api_key,
                        "origins": f"{origin[1]},{origin[0]}",
                        "destination": f"{destination[1]},{destination[0]}",
                        "type": "1",  # 驾车
                    },
                    timeout=5,
                )
                data = resp.json()
                if data.get("status") == "1" and data.get("results"):
                    r = data["results"][0]
                    return (int(r["distance"]) / 1000, int(r["duration"]) // 60)
            except Exception:
                pass

        # Fallback: Haversine 公式
        return self._haversine(origin, destination)

    @staticmethod
    def _haversine(
        coord_a: Tuple[float, float],
        coord_b: Tuple[float, float],
    ) -> Tuple[float, int]:
        """Haversine 球面距离计算"""
        lat1, lng1 = coord_a
        lat2, lng2 = coord_b
        R = 6371  # 地球半径 (km)

        dlat = math.radians(lat2 - lat1)
        dlng = math.radians(lng2 - lng1)
        a = (
            math.sin(dlat / 2) ** 2
            + math.cos(math.radians(lat1))
            * math.cos(math.radians(lat2))
            * math.sin(dlng / 2) ** 2
        )
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        distance_km = R * c

        # 估算耗时（驾车按 40km/h 城市速度）
        duration_min = int(distance_km / 40 * 60)
        return (round(distance_km, 2), max(duration_min, 5))

    # ========== 路线规划 ==========

    def plan_route(
        self,
        origin_name: str,
        dest_name: str,
        city: str = "北京",
        mode: str = "auto",
    ) -> RouteResult:
        """规划两点间的最佳路线

        Args:
            origin_name: 起点名称
            dest_name: 终点名称
            city: 城市
            mode: 出行方式 "auto"(自动推荐) | "walking" | "driving" | "transit"

        Returns:
            RouteResult
        """
        # 1. 地理编码
        coord_a = self.geocode(origin_name, city)
        coord_b = self.geocode(dest_name, city)

        if not coord_a or not coord_b:
            return RouteResult(
                distance_km=0,
                duration_min=0,
                transport="未知",
                route_detail=f"未找到 '{origin_name}' 或 '{dest_name}' 的坐标信息",
                source="fallback",
            )

        # 2. 计算距离
        distance_km, duration_min = self.get_distance(coord_a, coord_b)

        # 3. 推荐交通方式
        if mode == "auto":
            if distance_km < 1.0:
                transport = "步行"
                duration_min = int(distance_km / 5 * 60)  # 步行 5km/h
                route_detail = f"距离很近，步行约{duration_min}分钟即可到达"
            elif distance_km < 5.0:
                transport = "骑行/公交"
                duration_min = int(distance_km / 15 * 60)  # 公交 15km/h
                route_detail = f"距离较近，建议骑行或乘坐公交，约{duration_min}分钟"
            elif distance_km < 20.0:
                transport = "地铁"
                duration_min = int(distance_km / 30 * 60)  # 地铁 30km/h
                route_detail = f"建议乘坐地铁，约{duration_min}分钟"
            else:
                transport = "打车/驾车"
                route_detail = f"距离较远，建议打车或驾车前往，约{duration_min}分钟"
        elif mode == "walking":
            transport = "步行"
            route_detail = f"步行路线，约{duration_min}分钟"
        elif mode == "driving":
            transport = "驾车"
            route_detail = f"驾车路线，约{duration_min}分钟"
        else:
            transport = "公共交通"
            route_detail = f"公交/地铁，约{duration_min}分钟"

        source = "amap_api" if self.available else "fallback"

        return RouteResult(
            distance_km=distance_km,
            duration_min=duration_min,
            transport=transport,
            route_detail=route_detail,
            source=source,
        )

    # ========== 周边搜索 (POI) ==========

    def search_poi(
        self,
        location: Tuple[float, float],
        poi_type: str = "050000",  # 餐饮
        radius: int = 3000,
        keywords: str = "",
        limit: int = 10,
    ) -> List[Dict]:
        """搜索周边 POI

        Args:
            location: 中心点坐标 (lat, lng)
            poi_type: POI 类型代码
                050000: 餐饮
                060000: 购物
                080000: 住宿
                110000: 风景名胜
            radius: 搜索半径（米）
            keywords: 搜索关键词
            limit: 返回数量上限

        Returns:
            POI 列表
        """
        if not self.available:
            return []

        try:
            params = {
                "key": self.api_key,
                "location": f"{location[1]},{location[0]}",
                "types": poi_type,
                "radius": radius,
                "offset": limit,
                "extensions": "all",
            }
            if keywords:
                params["keywords"] = keywords

            resp = requests.get(
                f"{AMAP_BASE}/place/around",
                params=params,
                timeout=5,
            )
            data = resp.json()
            if data.get("status") == "1":
                return data.get("pois", [])
        except Exception:
            pass

        return []

    def search_restaurants(
        self,
        location: Tuple[float, float],
        keywords: str = "",
        radius: int = 3000,
        limit: int = 5,
    ) -> List[Dict]:
        """搜索周边餐厅"""
        return self.search_poi(
            location=location,
            poi_type="050000",
            radius=radius,
            keywords=keywords,
            limit=limit,
        )

    def search_hotels(
        self,
        location: Tuple[float, float],
        keywords: str = "",
        radius: int = 5000,
        limit: int = 5,
    ) -> List[Dict]:
        """搜索周边酒店"""
        return self.search_poi(
            location=location,
            poi_type="080000",
            radius=radius,
            keywords=keywords,
            limit=limit,
        )


# 全局单例
amap_service = AmapService()
