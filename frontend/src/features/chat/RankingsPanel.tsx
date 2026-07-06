/** 排名面板 — 美食排行榜 + 酒店推荐榜（Tab 切换） */

import { useState } from "react";
import { useChatStore } from "../../stores/chatStore";
import { RankingList, HotelRankingList } from "../../components/RankingList/RankingList";
import { Tag } from "../../components/Tag/Tag";

type SubTab = "food" | "hotel";

export function RankingsPanel() {
  const { restaurantRankings, hotelRankings } = useChatStore();
  const [activeSubTab, setActiveSubTab] = useState<SubTab>("food");

  // 扁平化所有餐厅/酒店数据
  const allRestaurants = restaurantRankings.flat();
  const allHotels = hotelRankings.flat();

  const hasData = allRestaurants.length > 0 || allHotels.length > 0;

  if (!hasData) {
    return (
      <div className="flex-1 flex items-center justify-center py-12">
        <div className="text-center">
          <span className="text-4xl block mb-2">📊</span>
          <p className="text-body text-text-secondary">
            发送旅行需求后，美食和酒店排名将在此显示
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="flex flex-col h-full">
      {/* 子 Tab 切换 */}
      <div className="flex-shrink-0 flex gap-1 px-4 py-3 border-b border-divider">
        <Tag
          variant="primary"
          active={activeSubTab === "food"}
          onClick={() => setActiveSubTab("food")}
        >
          🍜 美食 ({allRestaurants.length})
        </Tag>
        <Tag
          variant="primary"
          active={activeSubTab === "hotel"}
          onClick={() => setActiveSubTab("hotel")}
        >
          🏨 酒店 ({allHotels.length})
        </Tag>
      </div>

      {/* 内容区 */}
      <div className="flex-1 overflow-y-auto px-3 py-3 space-y-3">
        {activeSubTab === "food" &&
          (allRestaurants.length > 0 ? (
            <RankingList items={allRestaurants} />
          ) : (
            <div className="text-center py-8 text-text-tertiary text-caption">
              暂未获取到餐厅数据
            </div>
          ))}

        {activeSubTab === "hotel" &&
          (allHotels.length > 0 ? (
            <HotelRankingList items={allHotels} />
          ) : (
            <div className="text-center py-8 text-text-tertiary text-caption">
              暂未获取到酒店数据
            </div>
          ))}
      </div>
    </div>
  );
}
