/** QQ 风格行程时间线组件
 *
 * 设计规范：
 * - 时间线主轴: border-l-2 border-primary/30 (30% 透明 primary 蓝)
 * - 节点圆点:   w-[14px] h-[14px] rounded-full bg-primary border-2 border-white
 * - 时间:      text-caption text-text-secondary
 * - 景点名:    text-body text-text-primary font-medium
 * - 时长标签:  Tag 组件 (default variant)
 * - 门票标签:  Tag 组件 (success variant, #07C160)
 * - 交通:      text-small text-primary (行间衔接箭头)
 */

import { Tag } from "../Tag/Tag";

export interface TimelineSpot {
  time: string;
  name: string;
  duration: string;
  price: number;
  transport?: string;
  nextSpot?: string;
  nextDistance?: string;
}

interface TimelineProps {
  spots: TimelineSpot[];
  dayLabel?: string;
  className?: string;
}

export function Timeline({ spots, dayLabel, className = "" }: TimelineProps) {
  if (!spots.length) return null;

  return (
    <div className={`card-enter ${className}`}>
      {dayLabel && (
        <h3 className="text-h3 text-text-primary mb-4">📅 {dayLabel}</h3>
      )}
      <div className="relative pl-8 border-l-2 border-primary/30 space-y-0">
        {spots.map((spot, i) => (
          <div key={i} className="relative pb-5 last:pb-0">
            {/* 时间线节点圆点 */}
            <div
              className="
                absolute -left-[calc(2rem+5px)] top-1
                w-[14px] h-[14px] rounded-full
                bg-primary border-2 border-white
                shadow-sm
              "
            />

            {/* 时间 */}
            <p className="text-caption text-text-secondary mb-1">
              {spot.time}
            </p>

            {/* 景点名 + 标签 */}
            <div className="flex items-center gap-2 flex-wrap">
              <p className="text-body text-text-primary font-medium">
                {spot.name}
              </p>
              <Tag>{spot.duration}</Tag>
              {spot.price > 0 && <Tag variant="success">¥{spot.price}</Tag>}
            </div>

            {/* 前往下一站的交通 */}
            {spot.transport && spot.nextSpot && (
              <p className="text-small text-primary mt-1.5 flex items-center gap-1">
                {spot.transport === "walking"
                  ? "🚶"
                  : spot.transport === "metro"
                    ? "🚇"
                    : "🚗"}
                <span className="text-text-tertiary">
                  → {spot.nextSpot}
                </span>
                {spot.nextDistance && (
                  <span className="text-text-tertiary">
                    ({spot.nextDistance})
                  </span>
                )}
              </p>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
