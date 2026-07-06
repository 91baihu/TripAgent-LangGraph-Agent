"""景点搜索工具 — V1 Mock 数据版，后续升级为景小游 RAG 检索"""

from langchain_core.tools import tool


@tool
def search_attractions(city: str, keyword: str = "") -> str:
    """搜索指定城市的景点信息。当用户询问某地有什么好玩的、某个景点的详情时调用。

    Args:
        city: 城市名，如 '北京'、'杭州'
        keyword: 搜索关键词，如 '亲子'、'博物馆'、'自然风光'
    """
    # V1.0：先用 mock 数据跑通流程
    attractions_db = {
        "北京": [
            {"name": "故宫博物院", "type": "历史文化", "duration": "4小时",
             "price": 60, "kid_friendly": True, "description": "世界最大的宫殿建筑群"},
            {"name": "中国科技馆", "type": "科技馆", "duration": "3小时",
             "price": 30, "kid_friendly": True, "description": "互动体验丰富的亲子科普场馆"},
            {"name": "颐和园", "type": "园林", "duration": "3小时",
             "price": 30, "kid_friendly": True, "description": "皇家园林，适合散步游览"},
            {"name": "北京动物园", "type": "动物园", "duration": "3小时",
             "price": 15, "kid_friendly": True, "description": "亲子首选，有大熊猫馆"},
            {"name": "798艺术区", "type": "艺术区", "duration": "2小时",
             "price": 0, "kid_friendly": False, "description": "当代艺术展览，适合年轻人"},
        ],
        "杭州": [
            {"name": "西湖", "type": "自然风光", "duration": "半天",
             "price": 0, "kid_friendly": True, "description": "世界文化遗产，免费开放"},
            {"name": "灵隐寺", "type": "宗教文化", "duration": "2小时",
             "price": 45, "kid_friendly": False, "description": "千年古刹，香火旺盛"},
            {"name": "杭州乐园", "type": "主题乐园", "duration": "全天",
             "price": 190, "kid_friendly": True, "description": "大型游乐场，亲子必去"},
        ]
    }

    city_data = attractions_db.get(city, [])
    if keyword:
        filtered = []
        for a in city_data:
            # 检查 name、type、description 是否包含关键词
            searchable = " ".join([a["name"], a["type"], a["description"]])
            if keyword in searchable:
                filtered.append(a)
            # "亲子"关键词特殊处理：匹配 kid_friendly == True
            elif keyword == "亲子" and a["kid_friendly"]:
                filtered.append(a)
        city_data = filtered

    if not city_data:
        return f"未找到{city}的景点信息"

    result = f"## {city}景点推荐\n\n"
    for i, attr in enumerate(city_data, 1):
        tags = " ".join(["👶亲子友好" if attr["kid_friendly"] else ""])
        result += (f"{i}. **{attr['name']}** | {attr['type']} | "
                   f"约{attr['duration']} | ¥{attr['price']}\n"
                   f"   {attr['description']} {tags}\n\n")
    return result
