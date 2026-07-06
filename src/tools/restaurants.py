"""美食搜索工具 — 高德地图 POI 搜索 + Mock 数据兜底"""

from langchain_core.tools import tool

from .amap_service import amap_service

# Mock 数据（当 API 不可用时的 fallback）
MOCK_RESTAURANTS = {
    "北京": [
        {"name": "四季民福烤鸭店(故宫店)", "type": "北京菜", "price_per_person": 150, "near": "故宫"},
        {"name": "铃木食堂(南锣鼓巷)", "type": "日料", "price_per_person": 80, "near": "南锣鼓巷"},
        {"name": "小吊梨汤(望京)", "type": "北京菜", "price_per_person": 90, "near": "798艺术区"},
        {"name": "聚宝源(牛街)", "type": "涮羊肉", "price_per_person": 110, "near": "牛街"},
        {"name": "大董烤鸭(工体)", "type": "北京菜", "price_per_person": 350, "near": "三里屯"},
        {"name": "护国寺小吃(护国寺街)", "type": "小吃", "price_per_person": 30, "near": "什刹海"},
    ],
    "杭州": [
        {"name": "楼外楼(孤山路)", "type": "杭帮菜", "price_per_person": 130, "near": "西湖"},
        {"name": "知味观(湖滨)", "type": "小吃", "price_per_person": 50, "near": "西湖"},
        {"name": "绿茶餐厅(灵隐路)", "type": "杭帮菜", "price_per_person": 70, "near": "灵隐寺"},
        {"name": "外婆家(湖滨银泰)", "type": "杭帮菜", "price_per_person": 65, "near": "西湖"},
        {"name": "老头儿油爆虾(武林路)", "type": "杭帮菜", "price_per_person": 80, "near": "武林广场"},
    ],
    "上海": [
        {"name": "南翔馒头店(豫园)", "type": "本帮菜", "price_per_person": 90, "near": "豫园"},
        {"name": "老正兴菜馆(福州路)", "type": "本帮菜", "price_per_person": 120, "near": "外滩"},
        {"name": "光明村大酒家(淮海路)", "type": "本帮菜", "price_per_person": 70, "near": "淮海路"},
        {"name": "小杨生煎(吴江路)", "type": "小吃", "price_per_person": 30, "near": "南京路"},
    ],
    "成都": [
        {"name": "蜀九香火锅(春熙路)", "type": "火锅", "price_per_person": 100, "near": "春熙路"},
        {"name": "陈麻婆豆腐(骡马市)", "type": "川菜", "price_per_person": 50, "near": "宽窄巷子"},
        {"name": "皇城老妈(天府广场)", "type": "火锅", "price_per_person": 130, "near": "天府广场"},
        {"name": "钟水饺(人民公园)", "type": "小吃", "price_per_person": 25, "near": "人民公园"},
    ],
    "西安": [
        {"name": "回民街贾三灌汤包", "type": "西北菜", "price_per_person": 50, "near": "回民街"},
        {"name": "长安大牌档(钟楼)", "type": "西北菜", "price_per_person": 80, "near": "钟楼"},
        {"name": "同盛祥泡馍(钟楼)", "type": "西北菜", "price_per_person": 45, "near": "钟楼"},
    ],
}


@tool
def search_restaurants(city: str, near_spot: str = "", budget_level: str = "中等") -> str:
    """搜索指定城市的美食和餐厅推荐。安排行程中的用餐时使用。

    优先通过高德地图 POI 搜索获取真实餐厅数据；
    API 不可用时自动降级为内置美食数据库。

    Args:
        city: 城市名，如 '北京'、'杭州'
        near_spot: 附近的景点名称，如 '故宫'
        budget_level: 预算等级，'经济'、'中等'、'高档'
    """
    budget_ranges = {"经济": (0, 60), "中等": (0, 200), "高档": (100, 9999)}

    # 尝试使用高德 POI 搜索
    search_location = near_spot if near_spot else city
    if amap_service.available:
        coord = amap_service.geocode(search_location, city)
        if coord:
            pois = amap_service.search_restaurants(
                location=coord,
                keywords=budget_level if budget_level == "高档" else "",
                limit=8,
            )
            if pois:
                location_desc = f"（{near_spot} 附近）" if near_spot else ""
                result = f"## {city} 美食推荐{location_desc}\n\n"
                if budget_level:
                    if near_spot:
                        result += f"*筛选条件：{near_spot} 周边 · {budget_level}预算 · 🛰️高德地图*\n\n"
                    else:
                        result += f"*{budget_level}预算 · 🛰️高德地图*\n\n"
                for i, p in enumerate(pois, 1):
                    name = p.get("name", "未知")
                    poi_type = p.get("type", "餐饮")
                    address = p.get("address", "")
                    rating = p.get("biz_ext", {}).get("rating", "")
                    cost = p.get("biz_ext", {}).get("cost", "")
                    distance = p.get("distance", "")
                    dist_str = f"{int(distance)}m" if distance else ""
                    rating_str = f" ⭐{rating}" if rating else ""
                    cost_str = f" 人均约¥{cost}" if cost else ""
                    result += (
                        f"{i}. **{name}** | {poi_type}{rating_str}{cost_str}\n"
                        f"   📍{address}  📏{dist_str}\n\n"
                    )
                return result

    # Fallback: 使用 mock 数据
    city_data = MOCK_RESTAURANTS.get(city, [])
    if near_spot:
        filtered = [r for r in city_data if near_spot in r.get("near", "")]
        if filtered:
            city_data = filtered

    if budget_level in budget_ranges:
        lo, hi = budget_ranges[budget_level]
        city_data = [r for r in city_data if lo <= r["price_per_person"] <= hi]

    if not city_data:
        return f"未找到{city}{near_spot}附近的餐厅推荐"

    source_tag = "内置数据"
    result = f"## {city} 美食推荐\n\n"
    if near_spot:
        result += f"*{near_spot} 附近 · {budget_level}预算 · {source_tag}*\n\n"
    for i, r in enumerate(city_data, 1):
        result += (
            f"{i}. **{r['name']}** | {r['type']} | "
            f"人均¥{r['price_per_person']} | 靠近{r['near']}\n"
        )
    return result
