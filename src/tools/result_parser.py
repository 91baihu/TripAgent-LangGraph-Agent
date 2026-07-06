"""工具结果结构化解析器 — 将 Agent Markdown 返回提取为 {坐标, 评分, 排名} 结构化 JSON

用于前端可视化（地图 Marker、排行榜卡片、时间线），前端不再解析纯文本。
"""

import re
from typing import Optional, List, Dict, Any

from .amap_service import amap_service, FALLBACK_COORDS


# ========== 路线结果解析 ==========

def parse_route_result(text: str, city: str = "北京") -> Dict[str, Any]:
    """解析 plan_route 工具的 Markdown 返回

    Args:
        text: plan_route 返回的 Markdown 文本
        city: 所在城市（用于坐标查找）

    Returns:
        {
            "type": "route",
            "spots": [{"name": str, "lat": float, "lng": float, "order": int}, ...],
            "distance_km": float,
            "duration_min": int,
            "transport": str,
            "polyline": str,  # "lng,lat;lng,lat;..."
        }
    """
    result: Dict[str, Any] = {
        "type": "route",
        "spots": [],
        "distance_km": 0.0,
        "duration_min": 0,
        "transport": "未知",
        "polyline": "",
    }

    # 提取标题中的景点名: "## 故宫 → 颐和园"
    title_match = re.search(r"##\s*(.+?)\s*→\s*(.+)", text)
    if title_match:
        spot_a_name = title_match.group(1).strip()
        spot_b_name = title_match.group(2).strip()
    else:
        # 回退：尝试从多行中提取
        lines = text.split("\n")
        spot_a_name = lines[0].lstrip("# ").split("→")[0].strip() if lines else ""
        spot_b_name = ""
        if "→" in lines[0] if lines else "":
            spot_b_name = lines[0].split("→")[1].strip() if "→" in lines[0] else ""

    # 提取表格数据 — 使用 [^*|]+ 避免非贪婪 + 零宽度星号问题
    dist_match = re.search(r"距离\s*\|\s*\*{0,2}([\d.]+)\s*km", text, re.IGNORECASE)
    dur_match = re.search(r"预计耗时\s*\|\s*\*{0,2}(\d+)\s*分钟", text, re.IGNORECASE)
    trans_match = re.search(r"推荐交通\s*\|\s*\*{0,2}([^*|\n]+)", text)

    if dist_match:
        result["distance_km"] = float(dist_match.group(1))
    if dur_match:
        result["duration_min"] = int(dur_match.group(1))
    if trans_match:
        result["transport"] = trans_match.group(1).strip().rstrip("*").strip()

    # 查找坐标
    spots = []
    for i, name in enumerate([spot_a_name, spot_b_name]):
        if not name:
            continue
        lat, lng = _get_coordinate(name)
        spots.append({
            "name": name,
            "lat": lat,
            "lng": lng,
            "order": i + 1,
        })

    result["spots"] = spots

    # 构建 polyline
    if len(spots) >= 2:
        result["polyline"] = ";".join(
            f"{s['lng']},{s['lat']}" for s in spots
        )

    return result


# ========== 餐厅结果解析 ==========

def parse_restaurant_result(text: str) -> Dict[str, Any]:
    """解析 search_restaurants 工具的 Markdown 返回

    Args:
        text: search_restaurants 返回的 Markdown 文本

    Returns:
        {
            "type": "restaurant_list",
            "city": str,
            "near_spot": str,
            "items": [
                {"rank": int, "name": str, "type": str, "rating": float,
                 "price_per_person": int, "distance_m": int, "address": str,
                 "lat": float, "lng": float},
                ...
            ]
        }
    """
    result: Dict[str, Any] = {
        "type": "restaurant_list",
        "city": "",
        "near_spot": "",
        "items": [],
    }

    # 提取城市名和附近景点: "## 北京 美食推荐（故宫 附近）" 或 "## 北京 美食推荐"
    header_match = re.search(r"##\s*(.+?)\s*美食推荐", text)
    if header_match:
        header = header_match.group(1).strip()
        result["city"] = header

    # 提取附近景点（支持多种格式）
    # 格式1: "（故宫 附近）"
    near_match = re.search(r"（(.+?)\s*附近）", text)
    if near_match:
        result["near_spot"] = near_match.group(1).strip()
    # 格式2: "*故宫 附近 · " 或 "*筛选条件：故宫 周边 · "
    if not result["near_spot"]:
        near_match = re.search(r"\*(?:筛选条件[：:])?\s*(.+?)\s*(?:附近|周边)", text)
        if near_match:
            result["near_spot"] = near_match.group(1).strip()

    # 解析每条餐厅
    items = _parse_poi_items(text, "restaurant")
    result["items"] = items

    return result


# ========== 酒店结果解析 ==========

def parse_hotel_result(text: str) -> Dict[str, Any]:
    """解析 search_hotels 工具的 Markdown 返回

    Args:
        text: search_hotels 返回的 Markdown 文本

    Returns:
        {
            "type": "hotel_list",
            "city": str,
            "near_spot": str,
            "items": [
                {"rank": int, "name": str, "type": str, "rating": float,
                 "price_per_night": int, "distance_m": int, "feature": str,
                 "lat": float, "lng": float},
                ...
            ]
        }
    """
    result: Dict[str, Any] = {
        "type": "hotel_list",
        "city": "",
        "near_spot": "",
        "items": [],
    }

    # 提取城市名
    header_match = re.search(r"##\s*(.+?)\s*酒店推荐", text)
    if header_match:
        result["city"] = header_match.group(1).strip()

    # 提取附近景点（支持多种格式）
    # 格式1: "（故宫 附近）"
    near_match = re.search(r"（(.+?)\s*附近）", text)
    if near_match:
        result["near_spot"] = near_match.group(1).strip()
    # 格式2: "*故宫 附近 · " 或 "*筛选条件：故宫 周边 · "
    if not result["near_spot"]:
        near_match = re.search(r"\*(?:筛选条件[：:])?\s*(.+?)\s*(?:附近|周边)", text)
        if near_match:
            result["near_spot"] = near_match.group(1).strip()

    # 解析每条酒店
    items = _parse_hotel_items(text)
    result["items"] = items

    return result


# ========== 内部辅助函数 ==========

def _get_coordinate(name: str) -> tuple:
    """获取地名的坐标（lat, lng）"""
    # 先查 hard-coded fallback
    if name in FALLBACK_COORDS:
        return FALLBACK_COORDS[name]
    # 再试模糊匹配
    coord = amap_service._fuzzy_geocode(name)
    if coord:
        return coord
    # 兜底：返回默认坐标（北京天安门）
    return (39.9042, 116.4074)


def _parse_poi_items(text: str, kind: str = "restaurant") -> List[Dict[str, Any]]:
    """通用 POI 行解析 — 处理餐厅列表

    支持的格式:
    - 高德 POI 格式: "1. **店名** | 类型 ⭐4.5 人均约¥150\n   📍地址  📏1200m"
    - Mock 数据格式: "1. **店名** | 类型 | 人均¥150 | 靠近景点"
    """
    items = []
    # 匹配每行: 序号. **名称** | ...
    # 使用更宽松的模式
    pattern = r"(\d+)\.\s*\*\*(.+?)\*\*\s*\|(.+)"
    matches = re.findall(pattern, text)

    for match in matches:
        rank = int(match[0])
        name = match[1].strip()
        details = match[2].strip()

        item: Dict[str, Any] = {
            "rank": rank,
            "name": name,
            "rating": 0.0,
            "price_per_person": 0,
            "distance_m": 0,
            "address": "",
            "type": "",
            "lat": 0.0,
            "lng": 0.0,
        }

        # 提取类型（第一个 | 前或第一个字段）
        type_parts = details.split("|")
        if type_parts:
            first_part = type_parts[0].strip()
            # 可能是纯类型，也可能含评分
            type_match = re.match(r"([^\d⭐]+)", first_part)
            if type_match:
                item["type"] = type_match.group(1).strip()

        # 提取评分
        rating_match = re.search(r"⭐\s*([\d.]+)", details)
        if rating_match:
            item["rating"] = float(rating_match.group(1))

        # 提取人均价格
        price_match = re.search(r"(?:人均约?|¥)\s*(\d+)", details)
        if price_match:
            item["price_per_person"] = int(price_match.group(1))

        # 提取距离
        dist_match = re.search(r"📏\s*([\d.]+)\s*(km|m)", details)
        if dist_match:
            dist_val = float(dist_match.group(1))
            if dist_match.group(2) == "km":
                item["distance_m"] = int(dist_val * 1000)
            else:
                item["distance_m"] = int(dist_val)

        # 提取地址
        addr_match = re.search(r"📍\s*(.+?)(?:\s*📏|\s*$|\n)", details)
        if addr_match:
            item["address"] = addr_match.group(1).strip()

        # 查找坐标
        lat, lng = _get_coordinate(name)
        item["lat"] = lat
        item["lng"] = lng

        items.append(item)

    return items


def _parse_hotel_items(text: str) -> List[Dict[str, Any]]:
    """解析酒店列表"""
    items = []
    pattern = r"(\d+)\.\s*\*\*(.+?)\*\*\s*\|(.+)"
    matches = re.findall(pattern, text)

    for match in matches:
        rank = int(match[0])
        name = match[1].strip()
        details = match[2].strip()

        item: Dict[str, Any] = {
            "rank": rank,
            "name": name,
            "rating": 0.0,
            "price_per_night": 0,
            "distance_m": 0,
            "type": "",
            "feature": "",
            "address": "",
            "lat": 0.0,
            "lng": 0.0,
        }

        # 提取类型
        type_match = re.match(r"([^|\d⭐]+)", details)
        if type_match:
            item["type"] = type_match.group(1).strip()

        # 提取评分
        rating_match = re.search(r"⭐\s*([\d.]+)", details)
        if rating_match:
            item["rating"] = float(rating_match.group(1))

        # 提取每晚价格
        price_match = re.search(r"¥\s*(\d+)\s*/晚", details)
        if price_match:
            item["price_per_night"] = int(price_match.group(1))

        # 提取距离
        dist_match = re.search(r"📏\s*([\d.]+)\s*(km|m)", details)
        if dist_match:
            dist_val = float(dist_match.group(1))
            if dist_match.group(2) == "km":
                item["distance_m"] = int(dist_val * 1000)
            else:
                item["distance_m"] = int(dist_val)

        # 提取特点和地址（第二行）
        next_line_match = re.search(
            rf"{re.escape(name)}\|.*\n\s*(.+?)(?:\n|$)", text
        )
        if next_line_match:
            extra = next_line_match.group(1).strip()
            addr_match = re.search(r"📍\s*(.+?)(?:\s*📏|\s*$)", extra)
            if addr_match:
                item["address"] = addr_match.group(1).strip()
            # 剩余部分作为特点
            if "📍" in extra:
                item["feature"] = extra.split("📍")[0].strip()
            else:
                item["feature"] = extra

        # 查找坐标
        lat, lng = _get_coordinate(name)
        item["lat"] = lat
        item["lng"] = lng

        items.append(item)

    return items


def extract_route_spots(trace: list) -> list:
    """从 Streamlit trace 中提取所有路线景点（用于地图渲染）"""
    spots = []
    seen = set()

    for step in trace:
        if step.get("action") == "🔧 调用工具" and step.get("tool") == "plan_route":
            input_args = step.get("input", {})
            spot_a = input_args.get("spot_a", "")
            spot_b = input_args.get("spot_b", "")

            if spot_a and spot_a not in seen:
                seen.add(spot_a)
                lat, lng = _get_coordinate(spot_a)
                spots.append({
                    "name": spot_a,
                    "lat": lat,
                    "lng": lng,
                    "order": len(spots) + 1,
                })
            if spot_b and spot_b not in seen:
                seen.add(spot_b)
                lat, lng = _get_coordinate(spot_b)
                spots.append({
                    "name": spot_b,
                    "lat": lat,
                    "lng": lng,
                    "order": len(spots) + 1,
                })

    return spots


def extract_restaurant_items(trace: list) -> list:
    """从 Streamlit trace 中提取餐厅数据（用于排名表格渲染）"""
    all_items = []

    for step in trace:
        if step.get("action") == "🔧 调用工具" and step.get("tool") == "search_restaurants":
            output = step.get("output", "")
            if output:
                parsed = parse_restaurant_result(output)
                all_items.extend(parsed.get("items", []))

    return all_items


def extract_hotel_items(trace: list) -> list:
    """从 Streamlit trace 中提取酒店数据"""
    all_items = []

    for step in trace:
        if step.get("action") == "🔧 调用工具" and step.get("tool") == "search_hotels":
            output = step.get("output", "")
            if output:
                parsed = parse_hotel_result(output)
                all_items.extend(parsed.get("items", []))

    return all_items
