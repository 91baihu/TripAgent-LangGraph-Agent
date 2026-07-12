/** 可视化面板中的实时路线地图
 *
 * 使用 useAmap hook，监听 chatStore.geoRoutes 变化，
 * 自动添加 Marker + Polyline + fitBounds。
 */

import { useEffect, useRef, useState } from "react";
import { useAmap, type Spot } from "../../hooks/useAmap";
import { useChatStore } from "../../stores/chatStore";
import { WeatherCard } from "../../components/WeatherCard/WeatherCard";
import { SvgRouteMap } from "./SvgRouteMap";

const MAP_CONTAINER_ID = "visual-panel-map";

export function MapPanel() {
  const { geoRoutes, weatherData } = useChatStore();
  const { loaded, addSpotMarker, addRoute, clearAll, fitBounds } =
    useAmap(MAP_CONTAINER_ID);
  const renderedRef = useRef("");
  const [loadTimeout, setLoadTimeout] = useState(false);
  const [amapFailed, setAmapFailed] = useState(false);

  useEffect(() => {
    if (loaded) {
      setLoadTimeout(false);
      // Amap SDK 加载成功后，3 秒后检查地图是否真正渲染了瓦片
      const healthTimer = setTimeout(() => {
        const container = document.getElementById(MAP_CONTAINER_ID);
        if (container) {
          const hasCanvas = container.querySelector("canvas");
          const hasImage = container.querySelector("img");
          if (!hasCanvas && !hasImage) {
            setAmapFailed(true);
          }
        }
      }, 3000);
      return () => clearTimeout(healthTimer);
    }
    const timer = setTimeout(() => {
      setLoadTimeout(true);
    }, 6000);
    return () => clearTimeout(timer);
  }, [loaded]);

  // 决定使用哪种地图
  const useSvgFallback = !loaded && loadTimeout || amapFailed;
  const showAmap = loaded && !amapFailed;

  // 监听 geoRoutes 变化，更新地图
  useEffect(() => {
    if (!showAmap || geoRoutes.length === 0) {
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
  }, [showAmap, geoRoutes, addSpotMarker, addRoute, clearAll, fitBounds]);

  // ========== 始终渲染地图容器（让 useAmap 能找到 DOM 元素） ==========
  return (
    <div className="flex-1 relative min-h-[200px]">
      {/* Amap 容器 — 始终在 DOM 中，仅 Amap 可用时可见 */}
      <div
        id={MAP_CONTAINER_ID}
        className="absolute inset-0"
        style={{ visibility: showAmap ? "visible" : "hidden" }}
      />

      {/* SVG 降级（Amap 不可用时） */}
      {useSvgFallback && <SvgRouteMap geoRoutes={geoRoutes} />}

      {/* 加载骨架（初始加载中） */}
      {!loaded && !loadTimeout && (
        <div className="absolute inset-0 bg-sand flex items-center justify-center">
          <div className="text-center">
            <div className="w-12 h-12 mx-auto mb-3 rounded-full bg-sand-dark animate-breathe" />
            <p className="text-caption text-ink-tertiary">地图加载中...</p>
          </div>
        </div>
      )}

      {/* 天气浮层 */}
      {weatherData && (
        <WeatherCard
          weather={weatherData}
          variant="compact"
          className="absolute top-3 right-3 z-10"
        />
      )}

      {/* 空状态（Amap 可用但无数据） */}
      {showAmap && geoRoutes.length === 0 && (
        <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
          <div className="text-center bg-white/85 backdrop-blur border border-black/5 rounded-card px-8 py-6 shadow-warm-sm">
            <span className="text-5xl block mb-3">🗺️</span>
            <p className="text-body text-ink-secondary font-medium">
              发送旅行需求后，路线地图将在此显示
            </p>
            <p className="text-small text-ink-tertiary mt-1.5">
              尝试描述你的旅行计划开始规划吧
            </p>
          </div>
        </div>
      )}
    </div>
  );
}
