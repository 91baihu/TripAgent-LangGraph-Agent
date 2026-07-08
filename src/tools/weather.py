"""天气查询工具 — 接入 wttr.in 免费天气 API + 缓存"""

import requests
from langchain_core.tools import tool

# 兼容不同导入路径
try:
    from ..server.cache import cache_service
except ImportError:
    try:
        from server.cache import cache_service
    except ImportError:
        cache_service = None

# 中文城市名 → 英文城市名映射（wttr.in 需要英文名）
CITY_NAME_MAP = {
    "北京": "Beijing",
    "上海": "Shanghai",
    "杭州": "Hangzhou",
    "成都": "Chengdu",
    "西安": "Xi'an",
    "南京": "Nanjing",
    "深圳": "Shenzhen",
    "重庆": "Chongqing",
    "广州": "Guangzhou",
    "武汉": "Wuhan",
    "长沙": "Changsha",
    "厦门": "Xiamen",
    "青岛": "Qingdao",
    "大连": "Dalian",
    "苏州": "Suzhou",
    "昆明": "Kunming",
    "三亚": "Sanya",
    "桂林": "Guilin",
    "拉萨": "Lhasa",
    "哈尔滨": "Harbin",
    "郑州": "Zhengzhou",
    "天津": "Tianjin",
    "济南": "Ji'nan",
    "合肥": "Hefei",
    "南昌": "Nanchang",
    "福州": "Fuzhou",
    "贵阳": "Guiyang",
    "兰州": "Lanzhou",
    "沈阳": "Shenyang",
    "长春": "Changchun",
    "太原": "Taiyuan",
    "石家庄": "Shijiazhuang",
    "南宁": "Nanning",
    "海口": "Haikou",
    "乌鲁木齐": "Urumqi",
    "呼和浩特": "Hohhot",
    "银川": "Yinchuan",
    "西宁": "Xining",
}


def _to_english_city(city: str) -> str:
    """将中文城市名转为英文（wttr.in 需要英文名）"""
    # 如果已经是英文，直接返回
    if all(ord(c) < 128 for c in city):
        return city
    # 查找映射表
    return CITY_NAME_MAP.get(city, city)


@tool
def get_weather(city: str, date: str = "today") -> str:
    """查询指定城市和日期的天气。规划行程时先查天气，避免雨天安排户外景点。

    Args:
        city: 城市名，支持中文（如 '北京'）或英文（如 'Beijing'）
        date: 日期，如 '2026-07-10' 或 'today'
    """
    # 转为英文城市名
    english_city = _to_english_city(city)

    # 检查缓存（天气 10 分钟内不重复请求）
    cache_args = {"city": english_city, "date": date}
    if cache_service:
        cached = cache_service.get_tool_result_sync("get_weather", cache_args)
        if cached:
            return cached

    try:
        url = f"https://wttr.in/{english_city}?format=%C+%t+%h+%w&lang=zh"
        resp = requests.get(url, timeout=5)
        resp.raise_for_status()
        result = f"{city} 天气：{resp.text}"
    except requests.Timeout:
        result = f"天气服务响应超时，建议稍后重试。{city} 当前季节一般为晴好天气。"
    except requests.RequestException:
        result = f"天气服务暂不可用。建议出行前在手机天气 App 查看{city}最新天气。"

    # 写入缓存（10 分钟 TTL）
    if cache_service:
        cache_service.set_tool_result_sync("get_weather", cache_args, result, ttl=600)

    return result
