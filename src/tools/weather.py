"""天气查询工具 — 和风天气 (主) + 彩云天气 (备) + wttr.in JSON (兜底) + 缓存

改造要点（参见 docs/09-天气API选型与调用组件方案.md）：
1. 主 API：和风天气 DevAPI（免费 1000 次/天，中文城市原生支持）
2. 备 API：彩云天气（免费 1000 次/天，分钟级降水预报）
3. 兜底：wttr.in ?format=j1（JSON 格式，不再用纯文本正则硬猜）
4. 输出：Markdown（LLM 可读）+ Embedded JSON（前端精确解析）
5. 数据：实时天气 + 24h 逐时 + 7 日预报 + AQI + 生活指数
"""

import json
import os
from typing import Optional
from dataclasses import dataclass, field, asdict

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


# ========== 天气代码标准化映射 ==========
# 将和风/彩云/wttr 三方的天气代码统一为内部标准，消除前端解析二义性
CONDITION_CODES = {
    100: "晴", 101: "多云", 102: "少云", 103: "晴间多云",
    104: "阴",
    200: "风", 201: "大风",
    300: "阵雨", 301: "强阵雨", 302: "雷阵雨", 303: "强雷阵雨",
    304: "雷阵雨伴有冰雹",
    305: "小雨", 306: "中雨", 307: "大雨", 308: "暴雨",
    309: "大暴雨", 310: "特大暴雨",
    400: "小雪", 401: "中雪", 402: "大雪", 403: "暴雪",
    500: "雾", 501: "霾",
    900: "热", 901: "冷",
}


# ========== 数据模型 ==========

@dataclass
class HourlyForecast:
    """逐小时预报"""
    time: str           # "2026-07-12T14:00"
    temp: int           # 32
    condition: str      # "晴"
    condition_code: int  # 100
    pop: int            # 降水概率 0-100
    wind_scale: int     # 风力等级


@dataclass
class DailyForecast:
    """逐日预报"""
    date: str            # "2026-07-13"
    sunrise: str         # "05:12"
    sunset: str          # "19:38"
    temp_high: int
    temp_low: int
    condition_day: str
    condition_code_day: int
    pop: int             # 降水概率
    uv_index: int


@dataclass
class WeatherResult:
    """标准化天气结果 — 统一和风/彩云/wttr 三种数据源"""
    city: str
    city_en: str = ""
    update_time: str = ""
    temp: int = 0
    feels_like: int = 0
    condition: str = "未知"
    condition_code: int = 100
    humidity: int = 0
    wind_scale: int = 0          # 风力等级 0-12
    wind_dir: str = ""
    wind_speed: float = 0.0      # km/h
    visibility: float = 10.0     # km
    pressure: int = 1013         # hPa
    uv_index: int = 0
    aqi: int = 0
    aqi_level: str = ""
    hourly: list = field(default_factory=list)     # list[HourlyForecast]
    daily: list = field(default_factory=list)      # list[DailyForecast]
    life_index: dict = field(default_factory=dict)  # {"穿衣": "薄外套", ...}
    source: str = "unknown"      # "hefeng" | "caiyun" | "wttr" | "fallback"


# ========== 城市坐标映射（供需要经纬度的 API 使用） ==========

CITY_COORDS = {
    "北京": (116.4074, 39.9042), "上海": (121.4737, 31.2304),
    "杭州": (120.1551, 30.2741), "成都": (104.0665, 30.5728),
    "西安": (108.9402, 34.3416), "南京": (118.7969, 32.0603),
    "深圳": (114.0579, 22.5431), "重庆": (106.5516, 29.5630),
    "广州": (113.2644, 23.1291), "武汉": (114.3054, 30.5931),
    "长沙": (112.9388, 28.2277), "厦门": (118.0894, 24.4798),
    "青岛": (120.3826, 36.0671), "大连": (121.6147, 38.9140),
    "苏州": (120.5853, 31.2978), "昆明": (102.8329, 24.8801),
    "三亚": (109.5082, 18.2528), "桂林": (110.2900, 25.2736),
    "拉萨": (91.1718, 29.6520), "哈尔滨": (126.5350, 45.8023),
    "郑州": (113.6654, 34.7579), "天津": (117.1902, 39.1252),
    "济南": (117.0009, 36.6758), "合肥": (117.2827, 31.8669),
    "南昌": (115.8579, 28.6820), "福州": (119.2965, 26.0745),
    "贵阳": (106.6302, 26.6470), "兰州": (103.8343, 36.0611),
    "沈阳": (123.4291, 41.7968), "长春": (125.3245, 43.8868),
    "太原": (112.5492, 37.8570), "石家庄": (114.5020, 38.0455),
    "南宁": (108.3200, 22.8240), "海口": (110.3312, 20.0319),
    "乌鲁木齐": (87.6168, 43.8256), "呼和浩特": (111.6708, 40.8183),
    "银川": (106.2782, 38.4664), "西宁": (101.7789, 36.6232),
}


# ========== 和风天气 API ==========

class HefengAPI:
    """和风天气 DevAPI 封装

    免费额度：1000 次/天
    注册地址：https://dev.qweather.com/
    环境变量：HEFENG_API_KEY
    """

    BASE = "https://devapi.qweather.com/v7"
    GEO_BASE = "https://geoapi.qweather.com/v2"

    def __init__(self, api_key: str = ""):
        self.api_key = api_key or os.getenv("HEFENG_API_KEY", "")

    @property
    def available(self) -> bool:
        return bool(self.api_key)

    def _get(self, endpoint: str, params: dict, base: str = "") -> Optional[dict]:
        """通用 GET 请求，自动附加 API Key"""
        params["key"] = self.api_key
        try:
            resp = requests.get(
                f"{(base or self.BASE)}/{endpoint}",
                params=params,
                timeout=5,
            )
            data = resp.json()
            if data.get("code") == "200":
                return data
        except Exception:
            pass
        return None

    def city_lookup(self, city_name: str) -> Optional[dict]:
        """城市搜索 → 获取 city_id

        Returns:
            {"name": "北京", "id": "101010100", "lat": "39.90", "lon": "116.41", ...}
        """
        result = self._get("city/lookup", {"location": city_name}, base=self.GEO_BASE)
        if result and result.get("location"):
            return result["location"][0]
        return None

    def get_current(self, city_id: str) -> Optional[dict]:
        """实时天气"""
        result = self._get("weather/now", {"location": city_id})
        return result.get("now") if result else None

    def get_7day(self, city_id: str) -> Optional[list]:
        """7 天逐日预报"""
        result = self._get("weather/7d", {"location": city_id})
        return result.get("daily") if result else None

    def get_24hourly(self, city_id: str) -> Optional[list]:
        """24 小时逐时预报"""
        result = self._get("weather/24h", {"location": city_id})
        return result.get("hourly") if result else None

    def get_aqi(self, city_id: str) -> Optional[dict]:
        """实时空气质量"""
        result = self._get("air/now", {"location": city_id})
        return result.get("now") if result else None

    def get_life_index(self, city_id: str) -> Optional[list]:
        """生活指数（穿衣/防晒/洗车等 15 项）"""
        result = self._get("indices/1d", {"location": city_id, "type": "0"})
        return result.get("daily") if result else None


# ========== 彩云天气 API ==========

class CaiyunAPI:
    """彩云天气 API 封装

    免费额度：1000 次/天
    注册地址：https://dashboard.caiyunapp.com/
    环境变量：CAIYUN_API_KEY
    """

    BASE = "https://api.caiyunapp.com/v2.6"

    def __init__(self, api_key: str = ""):
        self.api_key = api_key or os.getenv("CAIYUN_API_KEY", "")

    @property
    def available(self) -> bool:
        return bool(self.api_key)

    def get_weather(self, lng: float, lat: float) -> Optional[dict]:
        """获取完整天气数据（实时 + 预报 + 分钟降水 + 预警）

        Returns:
            {"realtime": {...}, "minutely": {...}, "hourly": {...}, "daily": {...}, "alert": [...]}
        """
        try:
            resp = requests.get(
                f"{self.BASE}/{self.api_key}/{lng},{lat}/weather",
                params={"alert": "true", "dailysteps": "7"},
                timeout=5,
            )
            data = resp.json()
            if data.get("status") == "ok":
                return data["result"]
        except Exception:
            pass
        return None


# ========== wttr.in 兜底（JSON 格式） ==========

def _fallback_wttr(city: str) -> WeatherResult:
    """wttr.in JSON 格式兜底 — 比旧版纯文本解析稳定得多"""
    CITY_MAP = {
        "北京": "Beijing", "上海": "Shanghai", "杭州": "Hangzhou",
        "成都": "Chengdu", "西安": "Xi'an", "南京": "Nanjing",
        "深圳": "Shenzhen", "重庆": "Chongqing", "广州": "Guangzhou",
        "武汉": "Wuhan", "长沙": "Changsha", "厦门": "Xiamen",
        "青岛": "Qingdao", "大连": "Dalian", "苏州": "Suzhou",
        "昆明": "Kunming", "三亚": "Sanya", "桂林": "Guilin",
        "拉萨": "Lhasa", "哈尔滨": "Harbin", "郑州": "Zhengzhou",
        "天津": "Tianjin", "济南": "Ji'nan", "合肥": "Hefei",
        "南昌": "Nanchang", "福州": "Fuzhou", "贵阳": "Guiyang",
        "兰州": "Lanzhou", "沈阳": "Shenyang", "长春": "Changchun",
        "太原": "Taiyuan", "石家庄": "Shijiazhuang", "南宁": "Nanning",
        "海口": "Haikou", "乌鲁木齐": "Urumqi", "呼和浩特": "Hohhot",
        "银川": "Yinchuan", "西宁": "Xining",
    }
    en = CITY_MAP.get(city, city)
    try:
        resp = requests.get(
            f"https://wttr.in/{en}?format=j1",
            timeout=5,
        )
        data = resp.json()
        current = data["current_condition"][0]
        weather_desc = current["weatherDesc"][0]["value"]

        return WeatherResult(
            city=city,
            city_en=en,
            update_time=current.get("localObsDateTime", ""),
            temp=int(current["temp_C"]),
            feels_like=int(current.get("FeelsLikeC", current["temp_C"])),
            condition=weather_desc,
            condition_code=100,
            humidity=int(current["humidity"]),
            wind_scale=int(float(current.get("windspeedKmph", 0))) // 10,
            wind_dir=current.get("winddir16Point", ""),
            wind_speed=float(current.get("windspeedKmph", 0)),
            visibility=float(current.get("visibility", 10)),
            pressure=int(current.get("pressure", 1013)),
            uv_index=int(current.get("uvIndex", 0)),
            aqi=0,
            aqi_level="",
            source="wttr",
        )
    except Exception:
        return WeatherResult(city=city, source="fallback")


# ========== 辅助函数 ==========

def _city_to_coord(city: str) -> Optional[tuple]:
    """城市名 → 经纬度（模糊匹配）

    供彩云天气等需要经纬度的 API 使用。
    后续可升级为动态调用高德地理编码 API。
    """
    for name, (lng, lat) in CITY_COORDS.items():
        if name in city or city in name:
            return (lng, lat)
    return None


def _speed_to_scale(speed_kmh: float) -> int:
    """风速 km/h → 蒲福风力等级 0-12"""
    if speed_kmh < 1:   return 0
    if speed_kmh < 6:   return 1
    if speed_kmh < 12:  return 2
    if speed_kmh < 20:  return 3
    if speed_kmh < 29:  return 4
    if speed_kmh < 39:  return 5
    if speed_kmh < 50:  return 6
    if speed_kmh < 62:  return 7
    if speed_kmh < 75:  return 8
    if speed_kmh < 89:  return 9
    if speed_kmh < 103: return 10
    if speed_kmh < 117: return 11
    return 12


def _caiyun_skycon(code: str) -> tuple:
    """彩云天气代码 → (中文天气, 标准化 condition_code)"""
    MAP = {
        "CLEAR_DAY": ("晴", 100),
        "CLEAR_NIGHT": ("晴", 100),
        "PARTLY_CLOUDY_DAY": ("多云", 101),
        "PARTLY_CLOUDY_NIGHT": ("多云", 101),
        "CLOUDY": ("阴", 104),
        "LIGHT_RAIN": ("小雨", 305),
        "MODERATE_RAIN": ("中雨", 306),
        "HEAVY_RAIN": ("大雨", 307),
        "STORM_RAIN": ("暴雨", 308),
        "LIGHT_SNOW": ("小雪", 400),
        "MODERATE_SNOW": ("中雪", 401),
        "HEAVY_SNOW": ("大雪", 402),
        "FOG": ("雾", 500),
        "HAZE": ("霾", 501),
        "WIND": ("风", 200),
        "SAND": ("沙尘", 502),
        "DUST": ("浮尘", 503),
    }
    return MAP.get(code, ("未知", 100))


def _parse_hourly(data: list, source: str = "hefeng") -> list:
    """解析逐时数据 → list[HourlyForecast]"""
    results = []
    for h in (data or []):
        if source == "caiyun":
            results.append(HourlyForecast(
                time=h.get("datetime", ""),
                temp=int(h.get("temperature", 0)),
                condition=_caiyun_skycon(h.get("skycon", ""))[0],
                condition_code=_caiyun_skycon(h.get("skycon", ""))[1],
                pop=int(float(h.get("precipitation", {}).get("probability", 0))
                       if isinstance(h.get("precipitation"), dict) else 0),
                wind_scale=_speed_to_scale(float(
                    h.get("wind", {}).get("speed", 0)
                    if isinstance(h.get("wind"), dict) else 0)),
            ))
        else:
            results.append(HourlyForecast(
                time=h.get("fxTime", ""),
                temp=int(h.get("temp", 0)),
                condition=CONDITION_CODES.get(int(h.get("icon", 100)), "未知"),
                condition_code=int(h.get("icon", 100)),
                pop=int(h.get("pop", 0)),
                wind_scale=int(h.get("windScale", 0)),
            ))
    return results


def _parse_daily(data: list, source: str = "hefeng") -> list:
    """解析逐日数据 → list[DailyForecast]"""
    results = []
    for d in (data or []):
        if source == "caiyun":
            skycon = d.get("skycon", "")
            condition, code = _caiyun_skycon(skycon)
            results.append(DailyForecast(
                date=d.get("date", ""),
                sunrise=d.get("astro", {}).get("sunrise", {}).get("time", "")
                    if isinstance(d.get("astro"), dict) else "",
                sunset=d.get("astro", {}).get("sunset", {}).get("time", "")
                    if isinstance(d.get("astro"), dict) else "",
                temp_high=int(d.get("temperature", {}).get("max", 0)
                             if isinstance(d.get("temperature"), dict) else 0),
                temp_low=int(d.get("temperature", {}).get("min", 0)
                            if isinstance(d.get("temperature"), dict) else 0),
                condition_day=condition,
                condition_code_day=code,
                pop=int(float(d.get("precipitation", {}).get("probability", 0))
                       if isinstance(d.get("precipitation"), dict) else 0),
                uv_index=int(d.get("life_index", {}).get("ultraviolet", [{}])[0].get("index", 0)
                            if isinstance(d.get("life_index"), dict)
                            and d.get("life_index", {}).get("ultraviolet") else 0),
            ))
        else:
            results.append(DailyForecast(
                date=d.get("fxDate", ""),
                sunrise=d.get("sunrise", ""),
                sunset=d.get("sunset", ""),
                temp_high=int(d.get("tempMax", 0)),
                temp_low=int(d.get("tempMin", 0)),
                condition_day=d.get("textDay", ""),
                condition_code_day=int(d.get("iconDay", 100)),
                pop=int(d.get("pop", 0)),
                uv_index=int(d.get("uvIndex", 0)),
            ))
    return results


# ========== 输出格式化 ==========

def _format_weather(w: WeatherResult) -> str:
    """将结构化天气数据格式化为 Markdown（LLM 可读）+ Embedded JSON（前端精确解析）"""

    # 序列化时，将 dataclass 对象转为 dict
    serializable = {
        **{k: v for k, v in asdict(w).items() if k not in ("hourly", "daily")},
        "hourly": [asdict(h) if hasattr(h, '__dataclass_fields__') else h for h in w.hourly],
        "daily": [asdict(d) if hasattr(d, '__dataclass_fields__') else d for d in w.daily],
    }
    json_block = json.dumps(serializable, ensure_ascii=False, indent=2)

    # --- Markdown 表格（LLM 友好） ---
    md = f"""## {w.city} 天气 · {w.condition}

| 指标 | 数值 |
|------|------|
| 🌡️ 当前温度 | **{w.temp}°C**（体感 {w.feels_like}°C） |
| ☁️ 天气状况 | {w.condition} |
| 💧 湿度 | {w.humidity}% |
| 🌬️ 风力 | {w.wind_dir} {w.wind_scale}级（{w.wind_speed}km/h） |
| 👁️ 能见度 | {w.visibility}km |
| 🌡️ 气压 | {w.pressure}hPa |
| ☀️ 紫外线 | {w.uv_index}级 |
| 🫁 空气质量 | AQI {w.aqi} · **{w.aqi_level}** |
"""

    # 生活指数
    if w.life_index:
        md += "\n### 🧭 生活建议\n"
        for name, level in w.life_index.items():
            md += f"- **{name}**: {level}\n"

    # 7 天预报表
    if w.daily:
        md += "\n### 📅 未来预报\n"
        md += "| 日期 | 天气 | 高温 | 低温 | 降水 | 紫外线 |\n"
        md += "|------|------|------|------|------|--------|\n"
        for d in w.daily[:7]:
            if hasattr(d, '__dataclass_fields__'):
                md += (f"| {d.date} | {d.condition_day} | "
                       f"{d.temp_high}°C | {d.temp_low}°C | "
                       f"{d.pop}% | {d.uv_index}级 |\n")
            else:
                md += (f"| {d['date']} | {d['condition_day']} | "
                       f"{d['temp_high']}°C | {d['temp_low']}°C | "
                       f"{d['pop']}% | {d['uv_index']}级 |\n")

    md += f"\n*数据来源：{w.source} · 更新于 {w.update_time}*\n"

    # 嵌入结构化 JSON（前端零歧义解析）
    md += f"\n<!-- WEATHER_JSON\n{json_block}\n-->"

    return md


# ========== 主工具函数 ==========

@tool
def get_weather(city: str, date: str = "today") -> str:
    """查询指定城市和日期的天气。规划行程时先查天气，避免雨天安排户外景点。

    三级降级策略：和风天气 → 彩云天气 → wttr.in
    返回结构化的 Markdown（人类可读）+ embedded JSON（前端精确解析）。

    Args:
        city: 城市名，支持中文（如 '北京'）或英文（如 'Beijing'）
        date: 日期，如 '2026-07-10' 或 'today'
    """
    # 1. 查缓存（天气 10 分钟内不重复请求）
    cache_key = {"city": city, "date": date}
    if cache_service:
        cached = cache_service.get_tool_result_sync("get_weather", cache_key)
        if cached:
            return cached

    # 2. 主路径：和风天气 API（中文城市原生支持、7 日预报、AQI、生活指数）
    weather = _try_hefeng(city)

    # 3. 备路径：彩云天气 API（分钟级降水、15 天预报、自研雷达外推）
    if not weather:
        weather = _try_caiyun(city)

    # 4. 兜底路径：wttr.in JSON 格式（无需 API Key，全球覆盖）
    if not weather:
        weather = _fallback_wttr(city)

    # 5. 格式化输出
    result = _format_weather(weather)

    # 6. 写缓存（10 分钟 TTL）
    if cache_service:
        cache_service.set_tool_result_sync("get_weather", cache_key, result, ttl=600)

    return result


def _try_hefeng(city: str) -> Optional[WeatherResult]:
    """尝试通过和风天气获取完整天气数据

    Returns:
        WeatherResult 若成功，None 若 API 不可用或城市未找到
    """
    api = HefengAPI()
    if not api.available:
        return None

    # Step 1: 城市名 → city_id
    location = api.city_lookup(city)
    if not location:
        return None

    city_id = location["id"]

    # Step 2: 拉取各维度数据
    current = api.get_current(city_id)
    if not current:
        return None

    daily_list = api.get_7day(city_id)
    hourly_list = api.get_24hourly(city_id)
    aqi_data = api.get_aqi(city_id)
    life_list = api.get_life_index(city_id)

    # Step 3: 组装生活指数
    life_index = {}
    if life_list:
        for item in life_list:
            name = item.get("name", "")
            category = item.get("category", "")
            if name and category:
                life_index[name] = category

    # Step 4: 标准化天气代码
    raw_icon = int(current.get("icon", 100))
    condition = CONDITION_CODES.get(raw_icon, current.get("text", "未知"))

    # Step 5: 构建标准化结果
    return WeatherResult(
        city=location.get("name", city),
        city_en=location.get("adm2", city),
        update_time=current.get("obsTime", ""),
        temp=int(current.get("temp", 0)),
        feels_like=int(current.get("feelsLike", 0)),
        condition=condition,
        condition_code=raw_icon,
        humidity=int(current.get("humidity", 0)),
        wind_scale=int(current.get("windScale", 0)),
        wind_dir=current.get("windDir", ""),
        wind_speed=float(current.get("windSpeed", 0)),
        visibility=float(current.get("vis", 10)),
        pressure=int(current.get("pressure", 1013)),
        uv_index=int((daily_list[0] if daily_list else {}).get("uvIndex", 0)),
        aqi=int((aqi_data or {}).get("aqi", 0)),
        aqi_level=(aqi_data or {}).get("category", ""),
        hourly=_parse_hourly(hourly_list, source="hefeng") if hourly_list else [],
        daily=_parse_daily(daily_list, source="hefeng") if daily_list else [],
        life_index=life_index,
        source="hefeng",
    )


def _try_caiyun(city: str) -> Optional[WeatherResult]:
    """尝试通过彩云天气获取完整天气数据（需经纬度）

    彩云的优势：分钟级降水预报（未来 2 小时）、自研雷达外推算法。

    Returns:
        WeatherResult 若成功，None 若 API 不可用或城市未找到
    """
    api = CaiyunAPI()
    if not api.available:
        return None

    # 城市 → 坐标（内置映射，后续可升级为高德地理编码 API 动态查询）
    coord = _city_to_coord(city)
    if not coord:
        return None

    lng, lat = coord
    data = api.get_weather(lng, lat)
    if not data:
        return None

    realtime = data.get("realtime", {})
    daily_data = data.get("daily", {})
    hourly_data = data.get("hourly", {})

    # 解析 AQI
    aqi_desc = (realtime.get("air_quality", {}) or {}).get("description", {}) or {}
    aqi = int(aqi_desc.get("aqi", 0))
    aqi_level = aqi_desc.get("quality", "")

    # 解析天气
    skycon = realtime.get("skycon", "")
    condition, condition_code = _caiyun_skycon(skycon)

    # 解析风力
    wind_info = realtime.get("wind", {}) or {}
    wind_speed_val = float(wind_info.get("speed", 0))
    wind_scale = _speed_to_scale(wind_speed_val)

    # 紫外线
    life_index_raw = daily_data.get("life_index", {}) or {}
    uv_list = life_index_raw.get("ultraviolet", [{}])
    uv_index = int(uv_list[0].get("index", 0)) if uv_list else 0

    # 解析逐日（彩云 daily 结构不同：temperature 是 [{"max":..,"min":..,"date":...}]）
    daily_temps = daily_data.get("temperature", [])
    daily_skycons = daily_data.get("skycon", [])
    daily_astro = daily_data.get("astro", [])
    daily_precip = daily_data.get("precipitation", [])

    daily_list = []
    for i in range(min(len(daily_temps), 7)):
        day_info = {
            "date": daily_temps[i].get("date", "") if i < len(daily_temps) else "",
            "temperature": daily_temps[i] if i < len(daily_temps) else {},
            "skycon": daily_skycons[i].get("value", "") if i < len(daily_skycons) else "",
            "astro": daily_astro[i] if i < len(daily_astro) else {},
            "precipitation": daily_precip[i] if i < len(daily_precip) else {},
            "life_index": daily_data.get("life_index", {}),
        }
        daily_list.append(day_info)

    # 解析逐时
    hourly_list = hourly_data.get("temperature", []) if hourly_data else []
    hourly_precip = hourly_data.get("precipitation", []) if hourly_data else {}
    hourly_skycons = hourly_data.get("skycon", []) if hourly_data else []
    hourly_wind = hourly_data.get("wind", []) if hourly_data else []

    hourly_parsed = []
    for i in range(min(len(hourly_list), 24)):
        h = {
            "datetime": hourly_list[i].get("datetime", "") if i < len(hourly_list) else "",
            "temperature": hourly_list[i].get("value", 0) if i < len(hourly_list) else 0,
            "skycon": hourly_skycons[i].get("value", "") if i < len(hourly_skycons) else "",
            "precipitation": hourly_precip[i] if i < len(hourly_precip) else {},
            "wind": hourly_wind[i] if i < len(hourly_wind) else {},
        }
        hourly_parsed.append(h)

    return WeatherResult(
        city=city,
        city_en="",
        update_time="",
        temp=int(realtime.get("temperature", 0)),
        feels_like=int(realtime.get("apparent_temperature", 0)),
        condition=condition,
        condition_code=condition_code,
        humidity=int(float(realtime.get("humidity", 0)) * 100),
        wind_scale=wind_scale,
        wind_dir="",
        wind_speed=wind_speed_val,
        visibility=float(realtime.get("visibility", 10)),
        pressure=0,
        uv_index=uv_index,
        aqi=aqi,
        aqi_level=aqi_level,
        hourly=_parse_hourly(hourly_parsed, source="caiyun") if hourly_parsed else [],
        daily=_parse_daily(daily_list, source="caiyun") if daily_list else [],
        life_index={},
        source="caiyun",
    )
