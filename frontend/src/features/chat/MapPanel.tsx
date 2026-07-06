/** 可视化面板中的实时路线地图
 *
 * 使用 useAmap hook，监听 chatStore.geoRoutes 变化，
 * 自动添加 Marker + Polyline + fitBounds。
 */

import { useEffect, useRef } from "react";
import { useAmap, type Spot } from "../../hooks/useAmap";
import { useChatStore } from "../../stores/chatStore";
import { WeatherCard } from "../../components/WeatherCard/WeatherCard";

const MAP_CONTAINER_ID = "visual-panel-map";

export function MapPanel() {
  const { geoRoutes, weatherData } = useChatStore();
  const { loaded, addSpotMarker, addRoute, clearAll, fitBounds } =
    useAmap(MAP_CONTAINER_ID);
  const renderedRef = useRef("");

  // 监听 geoRoutes 变化，更新地图
  useEffect(() => {
    if (!loaded || geoRoutes.length === 0) {
      renderedRef.current = "";
      return;
    }

    // 避免重复渲染相同的 routes
    const routeKey = JSON.stringify(geoRoutes);
    if (routeKey === renderedRef.current) return;

    clearAll();
    const allSpots: Spot[] = [];
    const seen = new Set<string>();

    for (const route of geoRoutes) {
      for (const spot of route.spots) {
        const key = `${spot.name}_${spot.lat.toFixed(4)}_${spot.lng.toFixed(4)}`;
        if (!seen.has(key)) {
          seen.add(key);
          allSpots.push(spot);
          addSpotMarker(spot);
        }
      }
    }

    // 绘制路线
    for (const route of geoRoutes) {
      for (let i = 0; i < route.spots.length - 1; i++) {
        addRoute(route.spots[i], route.spots[i + 1], route.transport);
      }
    }

    // 调整视野
    if (allSpots.length > 0) {
      fitBounds(allSpots);
    }

    renderedRef.current = routeKey;
  }, [loaded, geoRoutes, addSpotMarker, addRoute, clearAll, fitBounds]);

  if (!loaded) {
    return (
      <div className="flex-1 bg-surface-input flex items-center justify-center">
        <div className="text-center">
          <div className="w-12 h-12 mx-auto mb-3 skeleton-shimmer rounded-full" />
          <p className="text-caption text-text-tertiary">地图加载中...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="flex-1 relative min-h-[200px]">
      {/* Amap 容器 */}
      <div id={MAP_CONTAINER_ID} className="absolute inset-0" />

      {/* 天气浮层 */}
      {weatherData && (
        <WeatherCard
          weather={weatherData}
          compact
          className="absolute top-3 right-3 z-10"
        />
      )}

      {/* 空状态 */}
      {geoRoutes.length === 0 && (
        <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
          <div className="text-center bg-white/80 backdrop-blur px-6 py-4 rounded-card">
            <span className="text-4xl block mb-2">🗺️</span>
            <p className="text-body text-text-secondary">
              发送旅行需求后，路线地图将在此显示
            </p>
          </div>
        </div>
      )}
    </div>
  );
}
