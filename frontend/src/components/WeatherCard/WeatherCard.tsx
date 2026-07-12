/** 天气卡片 — 四种形态：Hero / Compact / Inline / Detail
 *
 * Hero:   渐变背景 + 粒子动效 + 大温度数字 + 三指标
 * Compact: 简洁浮层 (地图右上角)
 * Inline:  聊天气泡内单行
 */

import { useMemo } from "react";
import type { WeatherData } from "../../stores/chatStore";

// ========== 天气 → 视觉主题映射 ==========
interface WeatherTheme {
  bgClass: string;
  icon: string;
  effect: "sun" | "rain" | "snow" | "cloud" | "fog" | "storm" | null;
  textClass: string;
  label: string;
}

const WEATHER_THEMES: Record<string, WeatherTheme> = {
  "晴": { bgClass: "weather-bg-sunny", icon: "☀️", effect: "sun",   textClass: "text-amber-900", label: "晴朗" },
  "多云": { bgClass: "weather-bg-cloudy", icon: "⛅", effect: "cloud", textClass: "text-ink",      label: "多云" },
  "阴": { bgClass: "weather-bg-cloudy", icon: "☁️", effect: "cloud", textClass: "text-gray-700",  label: "阴天" },
  "雨": { bgClass: "weather-bg-rainy", icon: "🌧️", effect: "rain",  textClass: "text-slate-700", label: "雨天" },
  "阵雨": { bgClass: "weather-bg-rainy", icon: "🌦️", effect: "rain", textClass: "text-slate-700", label: "阵雨" },
  "小雨": { bgClass: "weather-bg-rainy", icon: "🌧️", effect: "rain", textClass: "text-slate-700", label: "小雨" },
  "中雨": { bgClass: "weather-bg-rainy", icon: "🌧️", effect: "rain", textClass: "text-slate-700", label: "中雨" },
  "大雨": { bgClass: "weather-bg-rainy", icon: "⛈️", effect: "rain", textClass: "text-slate-800", label: "大雨" },
  "雪": { bgClass: "weather-bg-snowy", icon: "❄️", effect: "snow",  textClass: "text-slate-600", label: "下雪" },
  "小雪": { bgClass: "weather-bg-snowy", icon: "🌨️", effect: "snow", textClass: "text-slate-600", label: "小雪" },
  "中雪": { bgClass: "weather-bg-snowy", icon: "❄️", effect: "snow", textClass: "text-slate-600", label: "中雪" },
  "雷": { bgClass: "weather-bg-stormy", icon: "⛈️", effect: "storm", textClass: "text-white",    label: "雷暴" },
  "雾": { bgClass: "weather-bg-foggy", icon: "🌫️", effect: "fog",   textClass: "text-ink-secondary", label: "有雾" },
  "霾": { bgClass: "weather-bg-foggy", icon: "😷", effect: "fog",   textClass: "text-ink-secondary", label: "雾霾" },
  "风": { bgClass: "weather-bg-cloudy", icon: "💨", effect: "cloud", textClass: "text-ink",      label: "大风" },
};

function matchTheme(condition: string): WeatherTheme {
  // 精确匹配
  if (WEATHER_THEMES[condition]) return WEATHER_THEMES[condition];
  // 模糊匹配
  for (const [key, theme] of Object.entries(WEATHER_THEMES)) {
    if (condition.includes(key) || key.includes(condition)) return theme;
  }
  return WEATHER_THEMES["晴"]!;
}

// ========== 温度解析 ==========
function parseTemp(tempStr: string): number {
  const match = tempStr?.match(/([+-]?\d+)/);
  return match ? parseInt(match[1], 10) : 20;
}

// ========== 温度条颜色 ==========
function tempBarClass(temp: number): string {
  if (temp < 5)  return "temp-bar-cold";
  if (temp < 15) return "temp-bar-cool";
  if (temp < 26) return "temp-bar-comfort";
  if (temp < 34) return "temp-bar-warm";
  return "temp-bar-hot";
}

// ========== 粒子动效组件 ==========

function SunParticles() {
  const particles = Array.from({ length: 10 }, (_, i) => ({
    id: i,
    left: `${5 + i * 9}%`,
    top: `${10 + (i % 3) * 28}%`,
    delay: `${i * 0.35}s`,
    size: i % 2 === 0 ? "3px" : "5px",
    driftX: `${15 + i * 5}px`,
    driftY: `${-(10 + i * 3)}px`,
  }));

  return (
    <div className="weather-particle-container" aria-hidden>
      {particles.map((p) => (
        <div
          key={p.id}
          className="sun-particle animate-sun-ray"
          style={{
            left: p.left,
            top: p.top,
            width: p.size,
            height: p.size,
            animationDelay: p.delay,
            ["--tw-drift-x" as string]: p.driftX,
            ["--tw-drift-y" as string]: p.driftY,
          } as React.CSSProperties}
        />
      ))}
    </div>
  );
}

function RainDrops() {
  const drops = Array.from({ length: 20 }, (_, i) => ({
    id: i,
    left: `${2 + i * 5}%`,
    delay: `${i * 0.11}s`,
    duration: `${0.55 + (i % 3) * 0.15}s`,
  }));

  return (
    <div className="weather-particle-container" aria-hidden>
      {drops.map((d) => (
        <div
          key={d.id}
          className="rain-drop animate-rain-drop"
          style={{
            left: d.left,
            top: "-20px",
            animationDelay: d.delay,
            animationDuration: d.duration,
          }}
        />
      ))}
    </div>
  );
}

function SnowFlakes() {
  const flakes = Array.from({ length: 15 }, (_, i) => ({
    id: i,
    left: `${3 + i * 6.5}%`,
    delay: `${i * 0.3}s`,
    duration: `${3 + (i % 3) * 1.5}s`,
    size: `${4 + (i % 3) * 3}px`,
  }));

  return (
    <div className="weather-particle-container" aria-hidden>
      {flakes.map((f) => (
        <div
          key={f.id}
          className="snow-flake animate-snow-fall"
          style={{
            left: f.left,
            top: "-10px",
            width: f.size,
            height: f.size,
            animationDelay: f.delay,
            animationDuration: f.duration,
          }}
        />
      ))}
    </div>
  );
}

function FogLayer() {
  return (
    <div className="weather-particle-container" aria-hidden>
      {[0, 1, 2].map((i) => (
        <div
          key={i}
          className="cloud-puff animate-cloud-drift"
          style={{
            width: `${80 + i * 40}px`,
            height: `${20 + i * 10}px`,
            left: `${-10 + i * 30}%`,
            top: `${25 + i * 20}%`,
            animationDelay: `${i * 1.5}s`,
            filter: `blur(${3 + i * 2}px)`,
          }}
        />
      ))}
    </div>
  );
}

function WeatherEffect({ effect }: { effect: WeatherTheme["effect"] }) {
  switch (effect) {
    case "sun":   return <SunParticles />;
    case "rain":  return <RainDrops />;
    case "snow":  return <SnowFlakes />;
    case "fog":   return <FogLayer />;
    case "storm": return <RainDrops />;
    case "cloud": return null;
    default:      return null;
  }
}

// ========== 温度进度条 ==========
function TempBar({ temp, max = 45 }: { temp: number; max?: number }) {
  const pct = Math.min(100, Math.max(0, (temp / max) * 100));
  return (
    <div className="w-full h-1.5 bg-white/30 rounded-full overflow-hidden">
      <div
        className={`h-full rounded-full transition-all duration-700 ${tempBarClass(temp)}`}
        style={{ width: `${pct}%` }}
      />
    </div>
  );
}

// ========== AQI 色标 ==========
function aqiColor(aqi: number): string {
  if (aqi <= 50)  return "bg-emerald-500";
  if (aqi <= 100) return "bg-yellow-500";
  if (aqi <= 150) return "bg-orange-500";
  if (aqi <= 200) return "bg-red-500";
  return "bg-purple-700";
}

function aqiLabel(aqi: number): string {
  if (aqi <= 50)  return "优";
  if (aqi <= 100) return "良";
  if (aqi <= 150) return "轻度";
  if (aqi <= 200) return "中度";
  if (aqi <= 300) return "重度";
  return "严重";
}

// ========== 7 日预报横条 ==========
function DailyStrip({ daily }: { daily: WeatherData["daily"] }) {
  if (!daily || daily.length === 0) return null;
  const WEATHER_ICONS: Record<string, string> = {
    "晴": "☀️", "多云": "⛅", "阴": "☁️", "少云": "🌤️",
    "小雨": "🌧️", "中雨": "🌧️", "大雨": "⛈️", "阵雨": "🌦️",
    "雷阵雨": "⛈️", "暴雨": "⛈️",
    "小雪": "🌨️", "中雪": "❄️", "大雪": "❄️",
    "雾": "🌫️", "霾": "😷", "风": "💨",
  };
  function iconFor(cond: string): string {
    for (const [key, icon] of Object.entries(WEATHER_ICONS)) {
      if (cond.includes(key)) return icon;
    }
    return "🌡️";
  }

  return (
    <div className="flex gap-1.5 mt-3 overflow-x-auto pb-1">
      {daily.slice(0, 7).map((d, i) => (
        <div
          key={i}
          className="flex-shrink-0 w-14 text-center rounded-lg bg-white/15 backdrop-blur py-2 px-1"
        >
          <p className="text-[0.6rem] opacity-60 leading-tight">
            {d.date?.slice(5) || ""}
          </p>
          <p className="text-sm my-0.5">{iconFor(d.condition_day || "")}</p>
          <p className="text-[0.65rem] font-semibold leading-tight">
            {d.temp_high}°
          </p>
          <p className="text-[0.6rem] opacity-50 leading-tight">{d.temp_low}°</p>
        </div>
      ))}
    </div>
  );
}

// ========== HERO 模式 ==========
function WeatherHero({ weather }: { weather: WeatherData }) {
  const temp = parseTemp(weather.temperature);
  const theme = matchTheme(weather.condition);
  const feelsLike = weather.feelsLike ?? temp;
  const aqi = weather.aqi;
  const aqiLevel = weather.aqiLevel || (aqi ? aqiLabel(aqi) : undefined);

  return (
    <div
      className={`
        relative overflow-hidden rounded-xl
        ${theme.bgClass} ${theme.textClass}
        p-5 transition-all duration-700
        shadow-warm-sm
      `}
    >
      <WeatherEffect effect={theme.effect} />

      {/* 内容 */}
      <div className="relative z-10">
        {/* 顶行：城市 + 天气标签 */}
        <div className="flex items-center justify-between mb-2">
          <p className="text-sm font-semibold tracking-wide opacity-70">
            📍 {weather.city}
          </p>
          <span className="text-xs font-semibold px-2.5 py-1 rounded-full bg-white/25 backdrop-blur">
            {theme.icon} {theme.label}
          </span>
        </div>

        {/* 温度大数字 */}
        <div className="flex items-baseline gap-1 my-2">
          <span className="text-[3.5rem] font-black leading-none font-serif animate-temp-pulse">
            {temp}
          </span>
          <span className="text-xl font-semibold opacity-60">°C</span>
        </div>

        {/* 温度条 */}
        <TempBar temp={temp} />

        {/* 体感描述 */}
        <p className="mt-2 text-sm opacity-60">
          体感 {feelsLike}°C · {weather.condition}
        </p>

        {/* 三指标图标行（v2 增强：AQI + 紫外线） */}
        <div className="flex gap-4 mt-3 text-xs opacity-70 flex-wrap">
          <span>💧 {weather.humidity}</span>
          <span>💨 {weather.wind}</span>
          {weather.uvIndex != null && weather.uvIndex > 0 && (
            <span>☀️ UV {weather.uvIndex}</span>
          )}
          {aqi != null && aqi > 0 && (
            <span className="inline-flex items-center gap-1">
              <span className={`inline-block w-2 h-2 rounded-full ${aqiColor(aqi)}`} />
              🫁 AQI {aqi} {aqiLevel}
            </span>
          )}
          {weather.daily && weather.daily.length > 0 && (
            <span>
              🌅 {weather.daily[0].sunrise || "--"}
            </span>
          )}
        </div>

        {/* 🆕 7 日预报横条 */}
        <DailyStrip daily={weather.daily} />

        {/* 🆕 生活指数 */}
        {weather.lifeIndex && Object.keys(weather.lifeIndex).length > 0 && (
          <div className="flex gap-2 mt-3 flex-wrap">
            {Object.entries(weather.lifeIndex).slice(0, 4).map(([name, level]) => (
              <span
                key={name}
                className="text-[0.65rem] px-2 py-0.5 rounded-full bg-white/20 backdrop-blur"
              >
                {name}: {level}
              </span>
            ))}
          </div>
        )}

        {/* 🆕 数据来源 */}
        {weather.source && (
          <p className="mt-3 text-[0.6rem] opacity-40 text-right">
            数据来源：{weather.source}
          </p>
        )}
      </div>
    </div>
  );
}

// ========== COMPACT 模式（地图浮层） ==========
function WeatherCompact({ weather }: { weather: WeatherData }) {
  const theme = matchTheme(weather.condition);
  const temp = parseTemp(weather.temperature);

  return (
    <div
      className="
        inline-flex items-center gap-2.5 px-3 py-2
        bg-white/85 backdrop-blur-xl border border-black/5
        rounded-lg shadow-warm-sm
      "
    >
      <span className="text-xl">{theme.icon}</span>
      <div className="leading-tight">
        <span className="text-lg font-extrabold text-ink">{temp}</span>
        <span className="text-xs font-semibold text-ink-tertiary ml-0.5">°C</span>
        <p className="text-[0.65rem] text-ink-secondary">{weather.city}</p>
      </div>
    </div>
  );
}

// ========== INLINE 模式（聊天气泡内） ==========
function WeatherInline({ weather }: { weather: WeatherData }) {
  const theme = matchTheme(weather.condition);
  return (
    <span className="inline-flex items-center gap-1.5 text-sm">
      <span>{theme.icon}</span>
      <span className="font-semibold text-ink">{weather.temperature}</span>
      <span className="text-ink-tertiary">{weather.city} · {weather.condition}</span>
    </span>
  );
}

// ========== DETAIL 模式（完整数据面板） ==========
function WeatherDetail({ weather }: { weather: WeatherData }) {
  const temp = parseTemp(weather.temperature);
  const theme = matchTheme(weather.condition);
  const feelsLike = weather.feelsLike ?? temp;
  const aqi = weather.aqi;

  return (
    <div className="bg-white rounded-xl border border-black/5 shadow-warm-sm overflow-hidden">
      {/* 头部：城市 + 温度 + 天气 */}
      <div className={`${theme.bgClass} ${theme.textClass} p-5 relative overflow-hidden`}>
        <WeatherEffect effect={theme.effect} />
        <div className="relative z-10">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-semibold opacity-70">📍 {weather.city}</p>
              <div className="flex items-baseline gap-1 mt-1">
                <span className="text-[3rem] font-black font-serif">{temp}</span>
                <span className="text-lg font-semibold opacity-60">°C</span>
              </div>
              <p className="text-sm opacity-60 mt-0.5">
                体感 {feelsLike}°C · {weather.condition}
              </p>
            </div>
            <span className="text-4xl">{theme.icon}</span>
          </div>
          {/* 温度条 */}
          <div className="mt-3">
            <TempBar temp={temp} />
          </div>
        </div>
      </div>

      {/* 指标网格 */}
      <div className="p-5 space-y-4">
        {/* 六项核心指标 */}
        <div className="grid grid-cols-3 gap-3 text-center">
          {[
            { label: "湿度", value: weather.humidity, icon: "💧" },
            { label: "风力", value: weather.wind, icon: "💨" },
            { label: "能见度", value: weather.visibility != null ? `${weather.visibility}km` : "--", icon: "👁️" },
            { label: "气压", value: weather.pressure != null ? `${weather.pressure}hPa` : "--", icon: "🌡️" },
            { label: "紫外线", value: weather.uvIndex != null ? `${weather.uvIndex}级` : "--", icon: "☀️" },
            {
              label: "AQI",
              value: aqi != null && aqi > 0 ? (
                <span className="inline-flex items-center gap-1">
                  <span className={`inline-block w-2 h-2 rounded-full ${aqiColor(aqi)}`} />
                  {aqi} {weather.aqiLevel || aqiLabel(aqi)}
                </span>
              ) : "--",
              icon: "🫁",
            },
          ].map(({ label, value, icon }) => (
            <div key={label} className="bg-cream rounded-lg p-2.5">
              <p className="text-lg mb-0.5">{icon}</p>
              <p className="text-xs text-ink-tertiary">{label}</p>
              <p className="text-sm font-semibold text-ink mt-0.5">{value}</p>
            </div>
          ))}
        </div>

        {/* 逐时预报横条 */}
        {weather.hourly && weather.hourly.length > 0 && (
          <div>
            <h4 className="text-xs font-semibold text-ink-tertiary uppercase tracking-wide mb-2">
              ⏱️ 逐时预报
            </h4>
            <div className="flex gap-1.5 overflow-x-auto pb-1">
              {weather.hourly.slice(0, 12).map((h, i) => (
                <div
                  key={i}
                  className="flex-shrink-0 w-12 text-center rounded-lg bg-cream py-2"
                >
                  <p className="text-[0.6rem] text-ink-tertiary">
                    {h.time?.slice(11, 16) || ""}
                  </p>
                  <p className="text-xs font-semibold text-ink mt-0.5">{h.temp}°</p>
                  <p className="text-[0.55rem] text-ink-tertiary">
                    {h.pop > 0 ? `${h.pop}%` : "·"}
                  </p>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* 7 日预报表 */}
        {weather.daily && weather.daily.length > 0 && (
          <div>
            <h4 className="text-xs font-semibold text-ink-tertiary uppercase tracking-wide mb-2">
              📅 7 日预报
            </h4>
            <div className="overflow-x-auto">
              <table className="w-full text-xs">
                <thead>
                  <tr className="text-ink-tertiary border-b border-black/5">
                    <th className="text-left py-1.5 font-medium">日期</th>
                    <th className="text-center py-1.5 font-medium">天气</th>
                    <th className="text-right py-1.5 font-medium">高/低温</th>
                    <th className="text-right py-1.5 font-medium">降水</th>
                    <th className="text-right py-1.5 font-medium">UV</th>
                  </tr>
                </thead>
                <tbody>
                  {weather.daily.slice(0, 7).map((d, i) => (
                    <tr key={i} className="border-b border-black/[0.03]">
                      <td className="py-1.5 text-ink-secondary">
                        {d.date?.slice(5) || ""}
                      </td>
                      <td className="py-1.5 text-center">{d.condition_day || "--"}</td>
                      <td className="py-1.5 text-right font-medium text-ink">
                        {d.temp_high}° / {d.temp_low}°
                      </td>
                      <td className="py-1.5 text-right text-ink-tertiary">
                        {d.pop > 0 ? `${d.pop}%` : "--"}
                      </td>
                      <td className="py-1.5 text-right text-ink-tertiary">
                        {d.uv_index > 0 ? `${d.uv_index}级` : "--"}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* 生活指数 */}
        {weather.lifeIndex && Object.keys(weather.lifeIndex).length > 0 && (
          <div>
            <h4 className="text-xs font-semibold text-ink-tertiary uppercase tracking-wide mb-2">
              🧭 生活建议
            </h4>
            <div className="flex gap-2 flex-wrap">
              {Object.entries(weather.lifeIndex).map(([name, level]) => (
                <span
                  key={name}
                  className="text-xs px-2.5 py-1 rounded-full bg-cream text-ink-secondary"
                >
                  {name}: <span className="font-medium text-ink">{level}</span>
                </span>
              ))}
            </div>
          </div>
        )}

        {/* 数据来源 */}
        {weather.source && (
          <p className="text-[0.65rem] text-ink-tertiary text-right">
            数据来源：{weather.source}
          </p>
        )}
      </div>
    </div>
  );
}

// ========== 导出 ==========
interface WeatherCardProps {
  weather: WeatherData;
  variant?: "hero" | "compact" | "inline" | "detail";
  className?: string;
}

export function WeatherCard({ weather, variant = "hero", className = "" }: WeatherCardProps) {
  if (variant === "compact") return <WeatherCompact weather={weather} />;
  if (variant === "inline")  return <WeatherInline weather={weather} />;
  if (variant === "detail")  return <WeatherDetail weather={weather} />;
  return (
    <div className={className}>
      <WeatherHero weather={weather} />
    </div>
  );
}
