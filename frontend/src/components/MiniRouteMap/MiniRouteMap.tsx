/** 对话中内嵌的迷你路线图
 *
 * 配色：spots → primary #12B7F5, route → primary 虚线
 * 在对话气泡流中实时展示路线概要，高度不超过 200px
 */

import { Card } from "../Card/Card";
import { Tag } from "../../components/Tag/Tag";
import type { Spot } from "../../hooks/useAmap";

interface MiniRouteProps {
  spots: Spot[];
  distance_km: number;
  transport: string;
}

export function MiniRouteMap({ spots, distance_km, transport }: MiniRouteProps) {
  if (!spots.length) return null;

  return (
    <div className="my-3 card-enter">
      <Card padding className="bg-primary-light/50">
        <p className="text-caption text-primary font-medium mb-2">
          🗺️ 路线规划结果
        </p>
        <div className="flex items-center gap-2 flex-wrap">
          {spots.map((spot, i) => (
            <span key={i} className="flex items-center gap-1">
              {i > 0 && (
                <span className="text-caption text-text-tertiary mx-1">
                  —{transport}→
                </span>
              )}
              <Tag variant="primary" active={i === 0}>
                ① {spot.name}
              </Tag>
            </span>
          ))}
        </div>
        <p className="text-small text-text-secondary mt-2">
          📏 距离：{distance_km}km · 🚗 {transport}
        </p>
      </Card>
    </div>
  );
}
