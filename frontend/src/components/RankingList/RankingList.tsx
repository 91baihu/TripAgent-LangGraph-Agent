/** QQ 风格餐厅排行榜卡片
 *
 * 设计规范：
 * 🥇 #1 → bg-[#FFF7E6] (暖金底) + border-amber-300
 * 🥈 #2 → bg-surface-input (#F0F1F3) (银灰底)
 * 🥉 #3 → bg-[#FFF0E0] (铜底)
 * 4-N → bg-surface-card (白底)
 *
 * 布局: flex row
 *   ├─ 排名圆: w-8 h-8 rounded-full (bg-primary #12B7F5)
 *   ├─ 餐厅信息列: 名称 + 类型 + 人均
 *   └─ 评分&距离: 右对齐 (⭐+数字 / 📍距离)
 */

import { Card } from "../Card/Card";

export interface RestaurantItem {
  rank: number;
  name: string;
  rating: number;
  price_per_person: number;
  distance_m: number;
  type: string;
  address: string;
}

export interface HotelItem {
  rank: number;
  name: string;
  rating: number;
  price_per_night: number;
  distance_m: number;
  type: string;
  feature: string;
  address: string;
}

const RANK_COLORS: Record<number, string> = {
  1: "bg-[#FFF7E6] border-amber-300",    // 🥇 暖金
  2: "bg-surface-input border-divider",   // 🥈 银灰
  3: "bg-[#FFF0E0] border-orange-200",    // 🥉 铜色
};

const RANK_BADGE_COLORS: Record<number, string> = {
  1: "bg-yellow-500 text-white",   // 🥇
  2: "bg-gray-400 text-white",     // 🥈
  3: "bg-amber-600 text-white",    // 🥉
};

const RANK_EMOJI: Record<number, string> = {
  1: "🥇",
  2: "🥈",
  3: "🥉",
};

function formatDistance(meters: number): string {
  if (meters >= 1000) {
    return `${(meters / 1000).toFixed(1)}km`;
  }
  return `${meters}m`;
}

function RankBadge({ rank }: { rank: number }) {
  const badgeClass =
    RANK_BADGE_COLORS[rank] || "bg-primary text-text-inverse";

  return (
    <span
      className={`
        w-8 h-8 rounded-full flex items-center justify-center
        text-small font-bold flex-shrink-0 ${badgeClass}
      `}
    >
      {rank}
    </span>
  );
}

/** 餐厅排行榜 */
export function RankingList({
  items,
  city,
}: {
  items: RestaurantItem[];
  city?: string;
}) {
  if (!items.length) return null;

  return (
    <div className="space-y-2 card-enter">
      <h3 className="text-h3 text-text-primary px-4 pt-2">
        🍜 {city ? `${city} ` : ""}美食排行榜
      </h3>
      {items.map((item) => {
        const bgClass =
          RANK_COLORS[item.rank] || "bg-surface-card border-divider";

        return (
          <Card key={item.rank} padding className={`border ${bgClass}`}>
            <div className="flex items-center gap-3">
              {/* 排名徽章 */}
              <span className="text-lg flex-shrink-0">
                {RANK_EMOJI[item.rank] || `#${item.rank}`}
              </span>

              {/* 餐厅信息 */}
              <div className="flex-1 min-w-0">
                <p className="text-body text-text-primary font-medium truncate">
                  {item.name}
                </p>
                <p className="text-caption text-text-secondary">
                  {item.type} · 人均 ¥{item.price_per_person}
                </p>
                {item.address && (
                  <p className="text-small text-text-tertiary mt-0.5">
                    📍 {item.address}
                  </p>
                )}
              </div>

              {/* 评分 & 距离 */}
              <div className="text-right flex-shrink-0">
                <p className="text-h3 text-semantic-warning font-bold">
                  ⭐ {item.rating}
                </p>
                <p className="text-small text-text-tertiary">
                  📍 {formatDistance(item.distance_m)}
                </p>
              </div>
            </div>
          </Card>
        );
      })}
    </div>
  );
}

/** 酒店排行榜 — 复用相同设计模式 */
export function HotelRankingList({
  items,
  city,
}: {
  items: HotelItem[];
  city?: string;
}) {
  if (!items.length) return null;

  return (
    <div className="space-y-2 card-enter">
      <h3 className="text-h3 text-text-primary px-4 pt-2">
        🏨 {city ? `${city} ` : ""}酒店推荐榜
      </h3>
      {items.map((item) => {
        const bgClass =
          RANK_COLORS[item.rank] || "bg-surface-card border-divider";

        return (
          <Card key={item.rank} padding className={`border ${bgClass}`}>
            <div className="flex items-center gap-3">
              {/* 排名徽章 */}
              <span className="text-lg flex-shrink-0">
                {RANK_EMOJI[item.rank] || `#${item.rank}`}
              </span>

              {/* 酒店信息 */}
              <div className="flex-1 min-w-0">
                <p className="text-body text-text-primary font-medium truncate">
                  {item.name}
                </p>
                <p className="text-caption text-text-secondary">
                  {item.type}
                  {item.price_per_night > 0
                    ? ` · ¥${item.price_per_night}/晚`
                    : " · 价格待询"}
                  {item.feature && ` · ${item.feature}`}
                </p>
                {item.address && (
                  <p className="text-small text-text-tertiary mt-0.5">
                    📍 {item.address}
                  </p>
                )}
              </div>

              {/* 评分 & 距离 */}
              <div className="text-right flex-shrink-0">
                <p className="text-h3 text-semantic-warning font-bold">
                  ⭐ {item.rating || "4.0"}
                </p>
                <p className="text-small text-text-tertiary">
                  📍 {formatDistance(item.distance_m)}
                </p>
              </div>
            </div>
          </Card>
        );
      })}
    </div>
  );
}
