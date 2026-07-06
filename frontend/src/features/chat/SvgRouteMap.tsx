/** SVG 降级路线图 — 当高德 JS SDK 不可用时自动激活
 *
 * 纯前端渲染，无需外部服务。将 geoRoutes 中的坐标映射到 SVG 画布。
 */

import { useChatStore, type GeoRouteData } from "../../stores/chatStore";
import { WeatherCard } from "../../components/WeatherCard/WeatherCard";

interface SvgRouteMapProps {
  geoRoutes: GeoRouteData[];
}

function mapCoords(routes: GeoRouteData[]) {
  const allSpots = routes.flatMap((r) => r.spots);
  if (allSpots.length === 0) return { spots: [], lines: [], viewBox: "0 0 400 300" };

  const lats = allSpots.map((s) => s.lat);
  const lngs = allSpots.map((s) => s.lng);
  const minLat = Math.min(...lats);
  const maxLat = Math.max(...lats);
  const minLng = Math.min(...lngs);
  const maxLng = Math.max(...lngs);

  const latRange = maxLat - minLat || 0.02;
  const lngRange = maxLng - minLng || 0.02;

  const PAD = 0.12;
  const W = 500;
  const H = 350;
  const toX = (lng: number) => ((lng - minLng) / lngRange) * (1 - 2 * PAD) * W + PAD * W;
  const toY = (lat: number) => ((maxLat - lat) / latRange) * (1 - 2 * PAD) * H + PAD * H;

  const uniqueSpots = new Map<string, { name: string; x: number; y: number; order: number }>();
  for (const route of routes) {
    for (const spot of route.spots) {
      const key = `${spot.name}_${spot.order}`;
      if (!uniqueSpots.has(key)) {
        uniqueSpots.set(key, {
          name: spot.name,
          x: toX(spot.lng),
          y: toY(spot.lat),
          order: spot.order,
        });
      }
    }
  }

  const lines: { x1: number; y1: number; x2: number; y2: number; transport: string }[] = [];
  for (const route of routes) {
    for (let i = 0; i < route.spots.length - 1; i++) {
      const a = route.spots[i];
      const b = route.spots[i + 1];
      lines.push({
        x1: toX(a.lng),
        y1: toY(a.lat),
        x2: toX(b.lng),
        y2: toY(b.lat),
        transport: route.transport,
      });
    }
  }

  return { spots: Array.from(uniqueSpots.values()), lines, viewBox: `0 0 ${W} ${H}` };
}

export function SvgRouteMap({ geoRoutes }: SvgRouteMapProps) {
  const { weatherData } = useChatStore();
  const { spots, lines, viewBox } = mapCoords(geoRoutes);

  if (spots.length === 0) {
    return (
      <div className="flex-1 bg-surface-input flex items-center justify-center min-h-[200px]">
        <div className="text-center">
          <span className="text-4xl block mb-2">🗺️</span>
          <p className="text-body text-text-secondary">暂无路线数据</p>
          <p className="text-caption text-text-tertiary mt-1">
            发送旅行需求后将在此显示路线图
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="flex-1 relative min-h-[200px] bg-surface-page">
      <svg
        viewBox={viewBox}
        className="w-full h-full"
        style={{ minHeight: 200 }}
      >
        <defs>
          <marker
            id="svg-arrow"
            markerWidth="8"
            markerHeight="6"
            refX="8"
            refY="3"
            orient="auto"
          >
            <polygon points="0 0, 8 3, 0 6" fill="#0E9FD6" />
          </marker>
        </defs>

        {/* 背景网格 */}
        <pattern id="grid" width="40" height="40" patternUnits="userSpaceOnUse">
          <path d="M 40 0 L 0 0 0 40" fill="none" stroke="#e8e8e8" strokeWidth="0.5" />
        </pattern>
        <rect width="100%" height="100%" fill="url(#grid)" />

        {/* 路线 */}
        {lines.map((line, i) => (
          <line
            key={`line-${i}`}
            x1={line.x1}
            y1={line.y1}
            x2={line.x2}
            y2={line.y2}
            stroke="#0E9FD6"
            strokeWidth="2.5"
            strokeDasharray={line.transport === "步行" ? "none" : "6,3"}
            markerEnd="url(#svg-arrow)"
          />
        ))}

        {/* 景点标记 */}
        {spots.map((spot) => (
          <g key={`${spot.name}_${spot.order}`}>
            <circle
              cx={spot.x}
              cy={spot.y}
              r="14"
              fill="#12B7F5"
              stroke="white"
              strokeWidth="2.5"
            />
            <text
              x={spot.x}
              y={spot.y}
              textAnchor="middle"
              dy="0.35em"
              fill="white"
              fontSize="11"
              fontWeight="700"
            >
              {spot.order}
            </text>
            <text
              x={spot.x}
              y={spot.y + 26}
              textAnchor="middle"
              fill="#6B6F75"
              fontSize="10"
            >
              {spot.name.length > 5 ? spot.name.slice(0, 5) + "..." : spot.name}
            </text>
          </g>
        ))}
      </svg>

      {/* 天气浮层 */}
      {weatherData && (
        <WeatherCard
          weather={weatherData}
          compact
          className="absolute top-3 right-3 z-10"
        />
      )}
    </div>
  );
}
