"""美食搜索工具 — Mock 数据版，后续可接大众点评 API"""

from langchain_core.tools import tool

RESTAURANTS = {
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
}


@tool
def search_restaurants(city: str, near_spot: str = "", budget_level: str = "中等") -> str:
    """搜索指定城市的美食和餐厅推荐。安排行程中的用餐时使用。

    Args:
        city: 城市名，如 '北京'、'杭州'
        near_spot: 附近的景点名称，如 '故宫'
        budget_level: 预算等级，'经济'、'中等'、'高档'
    """
    city_data = RESTAURANTS.get(city, [])
    if near_spot:
        city_data = [r for r in city_data if near_spot in r.get("near", "")]

    # 根据预算等级筛选
    budget_ranges = {"经济": (0, 60), "中等": (0, 200), "高档": (100, 9999)}
    if budget_level in budget_ranges:
        lo, hi = budget_ranges[budget_level]
        city_data = [r for r in city_data if lo <= r["price_per_person"] <= hi]

    if not city_data:
        return f"未找到{city}{near_spot}附近的餐厅推荐"

    result = f"## {city}美食推荐\n\n"
    for i, r in enumerate(city_data, 1):
        result += f"{i}. **{r['name']}** | {r['type']} | 人均¥{r['price_per_person']} | 靠近{r['near']}\n"
    return result
