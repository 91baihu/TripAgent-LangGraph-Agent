/** 可视化面板容器 — 整合地图 + 排名 + 推理追踪
 *
 * 桌面端：右侧固定面板
 * 移动端：通过 ChatPage 的 ViewSwitcher 切换至此全屏视图
 */

import { useState } from "react";
import { useChatStore } from "../../stores/chatStore";
import { Tag } from "../../components/Tag/Tag";
import { MapPanel } from "./MapPanel";
import { RankingsPanel } from "./RankingsPanel";
import { ReasoningTrace } from "./ReasoningTrace";
import { WeatherCard } from "../../components/WeatherCard/WeatherCard";

type PanelTab = "map" | "rankings" | "trace";

const TABS: { key: PanelTab; label: string; icon: string }[] = [
  { key: "map", label: "地图", icon: "🗺️" },
  { key: "rankings", label: "排名", icon: "📊" },
  { key: "trace", label: "推理", icon: "🔍" },
];

interface VisualizationPanelProps {
  variant?: "desktop" | "mobile";
  initialTab?: PanelTab;
  onBack?: () => void;
}

export function VisualizationPanel({
  variant = "desktop",
  initialTab = "map",
  onBack,
}: VisualizationPanelProps) {
  const [activeTab, setActiveTab] = useState<PanelTab>(initialTab);
  const { geoRoutes, restaurantRankings, hotelRankings, toolSteps, weatherData } =
    useChatStore();

  // 统计各面板数据
  const routeCount = geoRoutes.length;
  const rankingCount =
    restaurantRankings.flat().length + hotelRankings.flat().length;
  const traceCount = toolSteps.length;

  const isMobile = variant === "mobile";

  return (
    <div className="flex flex-col h-full">
      {/* 顶部：返回按钮(移动端) + Tab 栏 */}
      <div
        className={`flex-shrink-0 flex items-center gap-2 px-3 py-2 border-b border-divider ${
          isMobile ? "pt-3" : ""
        }`}
      >
        {isMobile && onBack && (
          <button
            onClick={onBack}
            className="w-8 h-8 flex items-center justify-center text-text-secondary hover:text-text-primary mr-1"
          >
            ←
          </button>
        )}
        <div className="flex gap-1 flex-1">
          {TABS.map((tab) => {
            const count =
              tab.key === "map"
                ? routeCount
                : tab.key === "rankings"
                  ? rankingCount
                  : traceCount;
            return (
              <Tag
                key={tab.key}
                variant="primary"
                active={activeTab === tab.key}
                onClick={() => setActiveTab(tab.key)}
              >
                {tab.icon} {tab.label}
                {count > 0 && (
                  <span className="ml-1 text-small opacity-70">({count})</span>
                )}
              </Tag>
            );
          })}
        </div>
      </div>

      {/* 天气卡片（桌面端嵌入顶部） */}
      {weatherData && variant === "desktop" && (
        <div className="flex-shrink-0 px-3 pt-2">
          <WeatherCard weather={weatherData} />
        </div>
      )}

      {/* 面板内容 */}
      <div className="flex-1 min-h-0 flex flex-col">
        {activeTab === "map" && <MapPanel />}
        {activeTab === "rankings" && <RankingsPanel />}
        {activeTab === "trace" && <ReasoningTrace />}
      </div>
    </div>
  );
}
