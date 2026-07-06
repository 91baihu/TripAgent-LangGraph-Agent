"""酒店搜索工具 — 高德地图 POI 搜索 + Mock 数据兜底"""

from langchain_core.tools import tool

from .amap_service import amap_service

# Mock 数据（当 API 不可用时的 fallback）
MOCK_HOTELS = {
    "北京": [
        {"name": "北京饭店", "type": "五星级", "price_per_night": 800,
         "near": "故宫", "feature": "步行5分钟到故宫"},
        {"name": "王府井希尔顿", "type": "五星级", "price_per_night": 950,
         "near": "王府井", "feature": "地铁直达，家庭友好"},
        {"name": "全季酒店(前门店)", "type": "经济型", "price_per_night": 280,
         "near": "天安门", "feature": "性价比高，交通便利"},
        {"name": "北京诺富特和平宾馆", "type": "四星级", "price_per_night": 500,
         "near": "王府井", "feature": "国际连锁，品质保障"},
        {"name": "北京798艺术酒店", "type": "精品酒店", "price_per_night": 420,
         "near": "798艺术区", "feature": "文艺风格，设计感强"},
    ],
    "杭州": [
        {"name": "杭州西湖希尔顿嘉悦里", "type": "五星级", "price_per_night": 700,
         "near": "西湖", "feature": "西湖景观房"},
        {"name": "杭州民宿(灵隐寺附近)", "type": "民宿", "price_per_night": 300,
         "near": "灵隐寺", "feature": "禅意氛围，静谧舒适"},
        {"name": "亚朵酒店(西湖文化广场)", "type": "中档型", "price_per_night": 350,
         "near": "西湖", "feature": "阅读空间，文化氛围"},
        {"name": "杭州洲际酒店", "type": "五星级", "price_per_night": 900,
         "near": "钱塘江", "feature": "大金球建筑，钱塘江景"},
        {"name": "汉庭酒店(杭州东站)", "type": "经济型", "price_per_night": 180,
         "near": "杭州东站", "feature": "性价比之选，交通枢纽"},
    ],
    "上海": [
        {"name": "上海和平饭店", "type": "五星级", "price_per_night": 1200, "near": "外滩", "feature": "外滩江景，历史建筑"},
        {"name": "全季酒店(南京东路)", "type": "经济型", "price_per_night": 320, "near": "南京路", "feature": "步行至外滩"},
        {"name": "上海浦东香格里拉", "type": "五星级", "price_per_night": 1100, "near": "陆家嘴", "feature": "江景房，地铁直达"},
    ],
    "成都": [
        {"name": "成都博舍", "type": "精品酒店", "price_per_night": 880, "near": "太古里", "feature": "设计师酒店，市中心"},
        {"name": "全季酒店(春熙路)", "type": "经济型", "price_per_night": 260, "near": "春熙路", "feature": "商圈核心，交通便利"},
        {"name": "成都富力丽思卡尔顿", "type": "五星级", "price_per_night": 950, "near": "天府广场", "feature": "奢华体验，地铁旁"},
    ],
    "西安": [
        {"name": "西安索菲特传奇酒店", "type": "五星级", "price_per_night": 780, "near": "钟楼", "feature": "市中心，历史建筑"},
        {"name": "汉庭酒店(钟楼店)", "type": "经济型", "price_per_night": 180, "near": "钟楼", "feature": "位置绝佳，性价比高"},
        {"name": "西安W酒店", "type": "五星级", "price_per_night": 900, "near": "大雁塔", "feature": "现代设计，夜景壮观"},
    ],
    "南京": [
        {"name": "南京金陵饭店", "type": "五星级", "price_per_night": 650, "near": "新街口", "feature": "老牌五星，市中心"},
        {"name": "亚朵酒店(夫子庙)", "type": "中档型", "price_per_night": 380, "near": "夫子庙", "feature": "秦淮河畔，文化氛围"},
        {"name": "如家精选(中山陵)", "type": "经济型", "price_per_night": 200, "near": "中山陵", "feature": "景区周边，清净舒适"},
    ],
    "深圳": [
        {"name": "深圳瑞吉酒店", "type": "五星级", "price_per_night": 1000, "near": "京基100", "feature": "云端酒店，无敌城景"},
        {"name": "汉庭酒店(海岸城)", "type": "经济型", "price_per_night": 220, "near": "海岸城", "feature": "商圈旁，交通便利"},
        {"name": "深圳华侨城洲际", "type": "五星级", "price_per_night": 850, "near": "欢乐谷", "feature": "亲子友好，度假风格"},
    ],
    "重庆": [
        {"name": "重庆解放碑威斯汀", "type": "五星级", "price_per_night": 700, "near": "解放碑", "feature": "市中心，夜景绝佳"},
        {"name": "全季酒店(洪崖洞)", "type": "中档型", "price_per_night": 300, "near": "洪崖洞", "feature": "步行至洪崖洞"},
        {"name": "汉庭酒店(观音桥)", "type": "经济型", "price_per_night": 160, "near": "观音桥", "feature": "商圈枢纽，性价比高"},
    ],
}


@tool
def search_hotels(
    city: str,
    near_spot: str = "",
    budget_level: str = "中等",
    check_in: str = "",
    check_out: str = "",
) -> str:
    """搜索指定城市的酒店住宿推荐。规划行程住宿时使用。

    优先通过高德地图 POI 搜索获取真实酒店数据；
    API 不可用时自动降级为内置酒店数据库。

    Args:
        city: 城市名，如 '北京'、'杭州'
        near_spot: 附近的景点或商圈名称，如 '故宫'
        budget_level: 预算等级，'经济'、'中等'、'高档'/'豪华'
        check_in: 入住日期，如 '2026-07-10'（可选）
        check_out: 离店日期，如 '2026-07-12'（可选）
    """
    budget_ranges = {
        "经济": (0, 300),
        "中等": (100, 600),
        "高档": (400, 99999),
        "豪华": (400, 99999),
    }

    # 尝试使用高德 POI 搜索
    if amap_service.available and near_spot:
        coord = amap_service.geocode(near_spot, city)
        if coord:
            pois = amap_service.search_hotels(
                location=coord,
                limit=8,
            )
            if pois:
                date_info = ""
                if check_in:
                    date_info += f"入住：{check_in}"
                if check_out:
                    date_info += f" | 离店：{check_out}"
                result = f"## {city} 酒店推荐（{near_spot} 附近）\n\n"
                if date_info:
                    result += f"*{date_info}*\n\n"
                result += f"*数据来源：🛰️高德地图*\n\n"
                for i, p in enumerate(pois, 1):
                    name = p.get("name", "未知")
                    poi_type = p.get("type", "住宿")
                    address = p.get("address", "")
                    rating = p.get("biz_ext", {}).get("rating", "")
                    distance = p.get("distance", "")
                    dist_str = f"{int(distance)}m" if distance else ""
                    rating_str = f" ⭐{rating}" if rating else ""
                    tel = p.get("tel", "")
                    tel_str = f" | 📞{tel}" if tel else ""
                    result += (
                        f"{i}. **{name}** | {poi_type}{rating_str}\n"
                        f"   📍{address}  📏{dist_str}{tel_str}\n"
                        f"   💰价格请电话咨询\n\n"
                    )
                return result

    # Fallback: 使用 mock 数据
    city_data = MOCK_HOTELS.get(city, [])
    if near_spot:
        filtered = [h for h in city_data if near_spot in h.get("near", "")]
        if filtered:  # 有精确匹配就用精确的
            city_data = filtered
        # 否则返回所有该城市酒店（不强制过滤）

    if budget_level in budget_ranges:
        lo, hi = budget_ranges[budget_level]
        city_data = [h for h in city_data if lo <= h["price_per_night"] <= hi]

    if not city_data:
        return f"未找到{city}{near_spot}附近的酒店推荐"

    date_info = ""
    if check_in:
        date_info += f"入住：{check_in}"
    if check_out:
        date_info += f" | 离店：{check_out}"

    result = f"## {city} 酒店推荐\n\n"
    if near_spot:
        result += f"*{near_spot} 附近 · {budget_level}预算 · 内置数据*\n\n"
    if date_info:
        result += f"*{date_info}*\n\n"

    for i, h in enumerate(city_data, 1):
        nights = 1
        if check_in and check_out:
            from datetime import datetime
            try:
                d1 = datetime.strptime(check_in, "%Y-%m-%d")
                d2 = datetime.strptime(check_out, "%Y-%m-%d")
                nights = max(1, (d2 - d1).days)
            except ValueError:
                pass
        total_cost = h["price_per_night"] * nights
        result += (
            f"{i}. **{h['name']}** | {h['type']} | "
            f"¥{h['price_per_night']}/晚\n"
            f"   {h['feature']} | {nights}晚预估 ¥{total_cost}\n\n"
        )
    return result
