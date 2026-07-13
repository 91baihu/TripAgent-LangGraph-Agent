/** 可视化面板中的实时路线地图
 *
 * 使用 useAmap hook，监听 chatStore.geoRoutes 变化，
 * 自动添加 Marker + Polyline + fitBounds。
 *
 * 增强功能：
 * - 路线信息面板（距离、时长、交通方式）
 * - 一键跳转高德导航
 * - 分段路线查看
 */

import { useEffect, useRef, useState } from "react";
import { useAmap, type Spot } from "../../hooks/useAmap";
import { useChatStore, type GeoRouteData } from "../../stores/chatStore";
import { WeatherCard } from "../../components/WeatherCard/WeatherCard";
import { SvgRouteMap } from "./SvgRouteMap";

const MAP_CONTAINER_ID = "visual-panel-map";

/** 生成高德地图导航 URL */
function buildAmapNavUrl(spots: Spot[]): string {
  if (spots.length < 2) return "#";
  const origin = `${spots[0].lng},${spots[0].lat}`;
  const dest = `${spots[spots.length - 1].lng},${spots[spots.length - 1].lat}`;
  const waypoints =
    spots.length > 2
      ? spots
          .slice(1, -1)
          .map((s) => `${s.lng},${s.lat}`)
          .join(";")
      : "";
  let url = `https://uri.amap.com/navigation?from=${origin}&to=${dest}`;
  if (waypoints) url += `&via=${waypoints}`;
  return url;
}

export function MapPanel() {
  const { geoRoutes, weatherData } = useChatStore();
  const { loaded, addSpotMarker, addRoute, clearAll, fitBounds } =
    useAmap(MAP_CONTAINER_ID);
  const renderedRef = useRef("");
  const [loadTimeout, setLoadTimeout] = useState(false);
  const [amapFailed, setAmapFailed] = useState(false);
  const [selectedRoute, setSelectedRoute] = useState<GeoRouteData | null>(null);

  useEffect(() => {
    if (loaded) {
      setLoadTimeout(false);
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
  const useSvgFallback = (!loaded && loadTimeout) || amapFailed;
  const showAmap = loaded && !amapFailed;

  // 监听 geoRoutes 变化，更新地图
  useEffect(() => {
    if (!showAmap || geoRoutes.length === 0) {
      renderedRef.current = "";
      return;
    }

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

    // 默认选中第一条路线
    if (geoRoutes.length > 0) {
      setSelectedRoute(geoRoutes[0]);
    }

    renderedRef.current = routeKey;
  }, [showAmap, geoRoutes, addSpotMarker, addRoute, clearAll, fitBounds]);

  // 空状态（Amap 可用但无数据）
  if (showAmap && geoRoutes.length === 0) {
    return (
      <div className="flex-1 relative min-h-[200px]">
        <div
          id={MAP_CONTAINER_ID}
          className="absolute inset-0"
          style={{ visibility: "visible" }}
        />
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
      </div>
    );
  }

  return (
    <div className="flex-1 relative min-h-[200px] flex flex-col">
      {/* Amap 容器 */}
      <div
        id={MAP_CONTAINER_ID}
        className="flex-1"
        style={{ visibility: showAmap ? "visible" : "hidden", minHeight: "200px" }}
      />

      {/* SVG 降级 */}
      {useSvgFallback && <SvgRouteMap geoRoutes={geoRoutes} />}

      {/* 加载骨架 */}
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

      {/* ===== 路线信息叠加面板 ===== */}
      {selectedRoute && geoRoutes.length > 0 && (
        <div className="absolute bottom-0 left-0 right-0 z-10 p-3">
          <div className="bg-white/90 backdrop-blur border border-warm-border2 rounded-card-lg p-3 shadow-warm-md animate-fade-up">
            {/* 路线概览 */}
            <div className="flex items-center justify-between mb-2">
              <h4 className="text-sm font-bold text-text-primary flex items-center gap-1">
                🗺️ 路线信息
              </h4>
              {/* 路线选择器（多路线时） */}
              {geoRoutes.length > 1 && (
                <div className="flex gap-1">
                  {geoRoutes.map((_, i) => (
                    <button
                      key={i}
                      onClick={() => setSelectedRoute(geoRoutes[i])}
                      className={`
                        w-5 h-5 text-[0.6rem] font-semibold rounded-full
                        border-none cursor-pointer transition-all
                        ${selectedRoute === geoRoutes[i]
                          ? "bg-ink text-white"
                          : "bg-sand-dark text-ink-tertiary hover:text-ink"
                        }
                      `}
                    >
                      {i + 1}
                    </button>
                  ))}
                </div>
              )}
            </div>

            {/* 统计信息 */}
            <div className="grid grid-cols-3 gap-2 mb-2">
              <div className="text-center">
                <div className="text-lg font-bold text-teal">
                  {selectedRoute.distance_km > 0
                    ? `${selectedRoute.distance_km.toFixed(1)}`
                    : "--"}
                </div>
                <div className="text-[0.6rem] text-ink-tertiary">公里</div>
              </div>
              <div className="text-center">
                <div className="text-lg font-bold text-teal">
                  {selectedRoute.duration_min > 0
                    ? `${selectedRoute.duration_min}`
                    : "--"}
                </div>
                <div className="text-[0.6rem] text-ink-tertiary">分钟</div>
              </div>
              <div className="text-center">
                <div className="text-lg font-bold text-teal">
                  {selectedRoute.transport || "步行"}
                </div>
                <div className="text-[0.6rem] text-ink-tertiary">交通</div>
              </div>
            </div>

            {/* 景点列表 */}
            <div className="flex flex-wrap gap-1 mb-2">
              {selectedRoute.spots.map((spot, i) => (
                <span
                  key={i}
                  className="inline-flex items-center gap-0.5 px-2 py-0.5 text-[0.65rem] font-medium bg-sand text-ink-secondary rounded-tag"
                >
                  <span className="w-4 h-4 rounded-full bg-teal text-white text-[0.55rem] flex items-center justify-center">
                    {spot.order || i + 1}
                  </span>
                  {spot.name}
                </span>
              ))}
            </div>

            {/* 一键跳转高德导航 */}
            <a
              href={buildAmapNavUrl(selectedRoute.spots)}
              target="_blank"
              rel="noopener noreferrer"
              className="
                w-full inline-flex items-center justify-center gap-1.5
                h-9 text-xs font-semibold text-white
                bg-gradient-to-r from-teal to-teal-dark
                rounded-button hover:opacity-90 active:scale-[0.97]
                transition-all no-underline cursor-pointer
              "
            >
              🧭 一键跳转高德导航
            </a>
          </div>
        </div>
      )}
    </div>
  );
}
