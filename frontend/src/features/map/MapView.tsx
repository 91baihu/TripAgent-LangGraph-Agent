/** 行程地图视图 — 完整高德交互地图
 *
 * 设计映射（来自项目 design-tokens）：
 * - 景点 Marker      → primary #12B7F5 圆形容器
 * - 路线 Polyline    → primary-hover #0E9FD6 虚线
 * - 步行路线         → semantic-success #07C160 实线
 * - 天气浮层         → surface-card #FFFFFF + shadow-card
 * - Day 切换器       → Tag 组件（primary variant）
 */

import { useState, useEffect, useCallback } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { Card } from "../../components/Card/Card";
import { Tag } from "../../components/Tag/Tag";
import { Button } from "../../components/Button/Button";
import { useAmap, type Spot } from "../../hooks/useAmap";
import { useChatStore } from "../../stores/chatStore";

interface DaySpot {
  time: string;
  name: string;
  duration: string;
  price: number;
  transport?: string;
  nextSpot?: string;
  nextDistance?: string;
}

interface DayData {
  label: string;
  spots: DaySpot[];
  routeSpots: Spot[];
}

/** 从 chatStore 的 geoRoutes 数据中提取各天路线景点 */
function buildDayData(): DayData[] {
  const { geoRoutes } = useChatStore.getState();

  if (geoRoutes.length === 0) {
    // 提供演示数据（实际使用时从 geo_data SSE 事件获取）
    return [];
  }

  // 将所有路线景点按序排列
  const allSpots: Spot[] = [];
  const seen = new Set<string>();
  for (const route of geoRoutes) {
    for (const spot of route.spots) {
      const key = `${spot.name}_${spot.lat}`;
      if (!seen.has(key)) {
        seen.add(key);
        allSpots.push({ ...spot, order: allSpots.length + 1 });
      }
    }
  }

  // 简单分组：每3-4个景点为一天
  const days: DayData[] = [];
  const spotsPerDay = Math.max(3, Math.ceil(allSpots.length / 3));
  for (let i = 0; i < allSpots.length; i += spotsPerDay) {
    const daySpots = allSpots.slice(i, i + spotsPerDay);
    days.push({
      label: `Day${days.length + 1}`,
      spots: daySpots.map((s) => ({
        time: "09:00",
        name: s.name,
        duration: "2h",
        price: 60,
      })),
      routeSpots: daySpots,
    });
  }

  return days;
}

export function MapView() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { addSpotMarker, addRoute, clearAll, fitBounds, loaded } =
    useAmap("amap-container");
  const [activeDay, setActiveDay] = useState(0);

  const [dayData] = useState<DayData[]>(() => buildDayData());
  const currentDay = dayData[activeDay];

  // 在地图上渲染当前天的景点和路线
  useEffect(() => {
    if (!loaded || !currentDay) return;

    clearAll();

    const spots = currentDay.routeSpots;
    // 添加标记
    spots.forEach((spot) => addSpotMarker(spot));

    // 添加路线
    for (let i = 0; i < spots.length - 1; i++) {
      addRoute(spots[i], spots[i + 1], i < spots.length - 2 ? "驾车" : "步行");
    }

    // 调整视野
    if (spots.length > 0) {
      fitBounds(spots);
    }
  }, [loaded, activeDay, currentDay, addSpotMarker, addRoute, clearAll, fitBounds]);

  // 平移地图到指定景点
  const focusSpot = useCallback(
    (spot: Spot) => {
      if (!window.AMap) return;
      // 通过调整地图中心
      const mapEl = document.getElementById("amap-container");
      if (mapEl) {
        mapEl.scrollIntoView({ behavior: "smooth" });
      }
    },
    []
  );

  const amapKey = import.meta.env.VITE_AMAP_JS_KEY;

  return (
    <div className="flex flex-col h-dvh bg-surface-page">
      {/* Header — h-14, bg-surface-card, border-b */}
      <header className="flex-shrink-0 h-14 bg-surface-card border-b border-divider flex items-center gap-3 px-4">
        <button
          onClick={() => navigate(-1)}
          className="w-8 h-8 flex items-center justify-center text-text-secondary hover:text-text-primary"
        >
          ←
        </button>
        <h1 className="text-h2 text-text-primary flex-1">行程地图</h1>
        {/* 天气浮层 */}
        <Tag variant="primary">☀️ 28°C 晴</Tag>
      </header>

      {/* 地图容器 — flex-1 填满剩余空间 */}
      {amapKey ? (
        <div id="amap-container" className="flex-1" />
      ) : (
        <div className="flex-1 bg-surface-input flex items-center justify-center">
          <div className="text-center p-6">
            <span className="text-5xl mb-4 block">🗺️</span>
            <p className="text-h3 text-text-primary mb-2">需要高德 JS API Key</p>
            <p className="text-body text-text-secondary mb-4">
              在 <code className="bg-surface-input px-1 rounded">.env</code> 中设置
              {" "}<code className="bg-surface-input px-1 rounded">VITE_AMAP_JS_KEY</code>
            </p>
            <ul className="text-left text-caption text-text-secondary space-y-1 mb-6">
              <li>· 前往高德控制台创建应用</li>
              <li>· 添加「JS API」服务</li>
              <li>· 将 Key 填入环境变量</li>
            </ul>
            <Button
              onClick={() => navigate(`/trips/${id}`)}
              variant="secondary"
            >
              返回行程详情
            </Button>
          </div>
        </div>
      )}

      {/* Day 切换器 — 复用 Tag 组件 */}
      {dayData.length > 0 && (
        <div className="flex-shrink-0 px-4 py-3 flex gap-2 bg-surface-card border-t border-divider overflow-x-auto">
          {dayData.map((day, i) => (
            <Tag
              key={day.label}
              variant="primary"
              active={i === activeDay}
              onClick={() => setActiveDay(i)}
            >
              {day.label}
            </Tag>
          ))}
        </div>
      )}

      {/* 底部行程卡片 — 复用 Card */}
      {currentDay && (
        <div className="flex-shrink-0 px-4 pb-6 pt-2 bg-surface-card">
          <Card padding className="shadow-card">
            {currentDay.spots.map((spot, i) => (
              <div
                key={i}
                className="relative pl-8 border-l-2 border-primary/30 pb-4 last:pb-0"
              >
                {/* 时间线节点圆点 */}
                <div
                  className="absolute -left-[calc(2rem+3px)] w-[14px] h-[14px]
                    rounded-full bg-primary border-2 border-white shadow-sm top-1"
                />
                <p className="text-caption text-text-secondary">{spot.time}</p>
                <p className="text-body text-text-primary font-medium">
                  {spot.name}
                </p>
                <div className="flex items-center gap-2 mt-1">
                  <Tag>{spot.duration}</Tag>
                  {spot.price > 0 && <Tag variant="success">¥{spot.price}</Tag>}
                </div>
                {spot.transport && (
                  <p className="text-small text-primary mt-1">
                    {spot.transport === "walking" ? "🚶" : "🚗"} →{" "}
                    {spot.nextSpot}{" "}
                    {spot.nextDistance && (
                      <span className="text-text-tertiary">
                        ({spot.nextDistance})
                      </span>
                    )}
                  </p>
                )}
              </div>
            ))}
          </Card>
        </div>
      )}
    </div>
  );
}
