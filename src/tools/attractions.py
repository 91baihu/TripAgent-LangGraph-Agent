"""景点搜索工具 — RAG 混合检索 (BM25 + BGE 向量) + Mock 数据兜底"""

from __future__ import annotations

from langchain_core.tools import tool

# 兼容 Streamlit (运行目录为 src/) 和 FastAPI (包导入) 两种方式
try:
    from ..rag.retriever import HybridRetriever
except ImportError:
    try:
        from rag.retriever import HybridRetriever
    except ImportError:
        HybridRetriever = None

# 延迟初始化检索器（避免模块导入时加载模型）
_retriever = None


def _get_retriever() -> HybridRetriever | None:
    """延迟初始化 HybridRetriever"""
    global _retriever
    if _retriever is None and HybridRetriever is not None:
        try:
            _retriever = HybridRetriever()
        except Exception:
            _retriever = None
    return _retriever


# V1 Mock 数据兜底（当 RAG 检索不可用时使用）
FALLBACK_ATTRACTIONS = {
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
    ],
    "上海": [
        {"name": "外滩", "type": "城市风光", "duration": "2小时",
         "price": 0, "kid_friendly": True, "description": "黄浦江畔万国建筑博览群"},
        {"name": "上海迪士尼乐园", "type": "主题乐园", "duration": "全天",
         "price": 475, "kid_friendly": True, "description": "中国大陆首座迪士尼乐园"},
        {"name": "上海科技馆", "type": "科技馆", "duration": "4小时",
         "price": 45, "kid_friendly": True, "description": "科普教育殿堂，互动体验丰富"},
    ],
    "成都": [
        {"name": "大熊猫繁育研究基地", "type": "动物园", "duration": "半天",
         "price": 55, "kid_friendly": True, "description": "近距离观察国宝大熊猫"},
        {"name": "宽窄巷子", "type": "历史文化", "duration": "2小时",
         "price": 0, "kid_friendly": True, "description": "老成都风貌，美食休闲好去处"},
        {"name": "锦里古街", "type": "历史文化", "duration": "2小时",
         "price": 0, "kid_friendly": True, "description": "三国文化主题仿古街"},
    ],
    "西安": [
        {"name": "兵马俑", "type": "历史文化", "duration": "半天",
         "price": 120, "kid_friendly": False, "description": "世界第八大奇迹"},
        {"name": "大雁塔", "type": "宗教文化", "duration": "2小时",
         "price": 50, "kid_friendly": True, "description": "唐代古塔，西安地标"},
        {"name": "西安城墙", "type": "历史文化", "duration": "3小时",
         "price": 54, "kid_friendly": True, "description": "中国现存最完整的古城墙"},
    ],
    "南京": [
        {"name": "中山陵", "type": "历史文化", "duration": "半天",
         "price": 0, "kid_friendly": True, "description": "孙中山先生陵寝，雄伟壮观"},
        {"name": "夫子庙", "type": "历史文化", "duration": "2小时",
         "price": 0, "kid_friendly": True, "description": "秦淮河畔，美食购物集中地"},
        {"name": "南京博物院", "type": "博物馆", "duration": "3小时",
         "price": 0, "kid_friendly": True, "description": "中国三大博物馆之一"},
    ],
    "重庆": [
        {"name": "洪崖洞", "type": "城市风光", "duration": "2小时",
         "price": 0, "kid_friendly": True, "description": "千与千寻同款吊脚楼，夜景绝美"},
        {"name": "磁器口古镇", "type": "历史文化", "duration": "2小时",
         "price": 0, "kid_friendly": True, "description": "千年古镇，美食小吃聚集地"},
        {"name": "长江索道", "type": "城市体验", "duration": "1小时",
         "price": 20, "kid_friendly": True, "description": "空中俯瞰两江交汇"},
    ],
    "深圳": [
        {"name": "世界之窗", "type": "主题乐园", "duration": "全天",
         "price": 220, "kid_friendly": True, "description": "世界名胜微缩景观公园"},
        {"name": "欢乐谷", "type": "主题乐园", "duration": "全天",
         "price": 230, "kid_friendly": True, "description": "大型现代化主题乐园"},
        {"name": "深圳湾公园", "type": "自然风光", "duration": "2小时",
         "price": 0, "kid_friendly": True, "description": "海滨休闲长廊，对面是香港"},
    ],
}


def _search_rag(city: str, keyword: str = "", top_k: int = 5) -> list[dict]:
    """使用 RAG 混合检索器搜索景点

    Returns:
        景点列表，格式兼容旧版 mock 数据结构
    """
    retriever = _get_retriever()
    if retriever is None:
        return []

    query = f"{city} {keyword}".strip()
    try:
        results = retriever.search(query, top_k=top_k)
    except Exception:
        return []

    attractions = []
    for doc in results:
        # 按城市过滤（如果检索结果来自其他城市）
        doc_city = doc.get("city", "")
        if city and doc_city and city not in doc_city and doc_city not in city:
            continue

        attractions.append({
            "name": doc.get("title", "未知景点"),
            "type": doc.get("type", "景点"),
            "duration": doc.get("duration", "2小时"),
            "price": doc.get("price", 0),
            "kid_friendly": doc.get("kid_friendly", True),
            "description": doc.get("content", "")[:80],
            "_source": "RAG检索",
        })

    return attractions


def _search_fallback(city: str, keyword: str = "") -> list[dict]:
    """从 Mock 数据中搜索景点（兜底方案）"""
    city_data = FALLBACK_ATTRACTIONS.get(city, [])

    if not city_data:
        return []

    if keyword:
        filtered = []
        for a in city_data:
            searchable = " ".join([a["name"], a["type"], a["description"]])
            if keyword in searchable:
                filtered.append(a)
            elif keyword == "亲子" and a["kid_friendly"]:
                filtered.append(a)
        city_data = filtered

    for a in city_data:
        a["_source"] = "内置数据"

    return city_data


def _format_results(city: str, attractions: list[dict]) -> str:
    """将景点列表格式化为 Markdown 输出"""
    if not attractions:
        return f"未找到{city}的景点信息"

    source_tag = attractions[0].get("_source", "") if attractions else ""

    result = f"## {city}景点推荐\n\n"
    if source_tag:
        result += f"*数据来源：{source_tag}*\n\n"

    for i, attr in enumerate(attractions, 1):
        tags = " ".join(["👶亲子友好" if attr.get("kid_friendly") else ""])
        result += (f"{i}. **{attr['name']}** | {attr.get('type', '')} | "
                   f"约{attr.get('duration', '')} | ¥{attr.get('price', 0)}\n"
                   f"   {attr.get('description', '')} {tags}\n\n")
    return result


@tool
def search_attractions(city: str, keyword: str = "") -> str:
    """搜索指定城市的景点信息。当用户询问某地有什么好玩的、某个景点的详情时调用。

    Args:
        city: 城市名，如 '北京'、'杭州'
        keyword: 搜索关键词，如 '亲子'、'博物馆'、'自然风光'
    """
    # 1. 优先使用 RAG 混合检索
    attractions = _search_rag(city, keyword)

    # 2. RAG 无结果 → 降级为 Mock 数据
    if not attractions:
        attractions = _search_fallback(city, keyword)

    return _format_results(city, attractions)
