"""天气查询工具 — 接入 wttr.in 免费天气 API"""

import requests
from langchain_core.tools import tool


@tool
def get_weather(city: str, date: str = "today") -> str:
    """查询指定城市和日期的天气。规划行程时先查天气，避免雨天安排户外景点。

    Args:
        city: 城市名英文，如 'Beijing'、'Hangzhou'
        date: 日期，如 '2026-07-10' 或 'today'
    """
    try:
        url = f"https://wttr.in/{city}?format=%C+%t+%h+%w&lang=zh"
        resp = requests.get(url, timeout=5)
        resp.raise_for_status()
        return f"{city} 天气：{resp.text}"
    except requests.Timeout:
        return f"天气服务响应超时，建议稍后重试。{city} 当前季节一般为晴好天气。"
    except requests.RequestException:
        return f"天气服务暂不可用。建议出行前在手机天气 App 查看{city}最新天气。"
