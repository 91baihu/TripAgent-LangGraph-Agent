/** 天气卡片 — 显示在可视化面板中 */

import type { WeatherData } from "../../stores/chatStore";

const WEATHER_ICONS: Record<string, string> = {
  "晴": "☀️",
  "多云": "⛅",
  "阴": "☁️",
  "雨": "🌧️",
  "雪": "❄️",
  "雷": "⛈️",
  "雾": "🌫️",
  "风": "💨",
};

function getWeatherIcon(condition: string): string {
  for (const [key, icon] of Object.entries(WEATHER_ICONS)) {
    if (condition.includes(key)) return icon;
  }
  return "🌤️";
}

interface WeatherCardProps {
  weather: WeatherData;
  compact?: boolean;
  className?: string;
}

export function WeatherCard({ weather, compact = false, className = "" }: WeatherCardProps) {
  const icon = getWeatherIcon(weather.condition);

  if (compact) {
    return (
      <div
        className={`
          inline-flex items-center gap-2 px-3 py-2
          bg-white/95 backdrop-blur rounded-card shadow-card
          ${className}
        `}
      >
        <span className="text-xl">{icon}</span>
        <div>
          <p className="text-h3 text-text-primary">{weather.temperature}</p>
          <p className="text-caption text-text-secondary">{weather.condition}</p>
        </div>
      </div>
    );
  }

  return (
    <div
      className={`
        bg-surface-card border border-divider rounded-card p-4 card-enter
        ${className}
      `}
    >
      <h3 className="text-h3 text-text-primary flex items-center gap-2 mb-3">
        <span>{icon}</span>
        🌤️ 天气详情
      </h3>
      <div className="grid grid-cols-2 gap-3">
        <div>
          <p className="text-caption text-text-tertiary">城市</p>
          <p className="text-body text-text-primary font-medium">
            {weather.city}
          </p>
        </div>
        <div>
          <p className="text-caption text-text-tertiary">温度</p>
          <p className="text-body text-text-primary font-medium">
            {weather.temperature}
          </p>
        </div>
        <div>
          <p className="text-caption text-text-tertiary">天气</p>
          <p className="text-body text-text-primary font-medium">
            {weather.condition}
          </p>
        </div>
        <div>
          <p className="text-caption text-text-tertiary">湿度</p>
          <p className="text-body text-text-primary font-medium">
            {weather.humidity}
          </p>
        </div>
        <div>
          <p className="text-caption text-text-tertiary">风力</p>
          <p className="text-body text-text-primary font-medium">
            {weather.wind}
          </p>
        </div>
      </div>
      {weather.details && !compact && (
        <details className="mt-3">
          <summary className="text-small text-primary cursor-pointer">
            查看详情
          </summary>
          <pre className="mt-1 p-2 bg-surface-input rounded-tag text-small text-text-secondary whitespace-pre-wrap max-h-[150px] overflow-y-auto">
            {weather.details}
          </pre>
        </details>
      )}
    </div>
  );
}
