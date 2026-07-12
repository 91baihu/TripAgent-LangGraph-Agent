/** 行程列表页 */

import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { Card } from "../../components/Card/Card";
import { Tag } from "../../components/Tag/Tag";
import { EmptyState } from "../../components/EmptyState/EmptyState";
import { TripCardSkeleton } from "../../components/Skeleton/Skeleton";
import { api } from "../../services/api";
import { endpoints } from "../../services/endpoints";

interface Trip {
  id: string;
  title: string;
  city: string;
  days: number;
  itinerary_json: Record<string, unknown>;
  status: string;
  created_at: string;
}

/** 城市名 → emoji 映射 */
const cityEmoji: Record<string, string> = {
  北京: "🏯",
  上海: "🌃",
  广州: "🌆",
  深圳: "🏙️",
  杭州: "🛶",
  成都: "🐼",
  西安: "🏛️",
  重庆: "🌉",
  南京: "🏯",
  武汉: "🌉",
  长沙: "🏙️",
  厦门: "🏖️",
  三亚: "🌴",
  大理: "🏔️",
  丽江: "🏘️",
  桂林: "⛰️",
  苏州: "🌿",
  青岛: "🍺",
  大连: "🌊",
  哈尔滨: "❄️",
};

function getCityEmoji(city: string): string {
  return cityEmoji[city] || "🏙️";
}

export function TripListPage() {
  const [trips, setTrips] = useState<Trip[]>([]);
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();

  useEffect(() => {
    api
      .get<{ trips: Trip[] }>(endpoints.trips.list)
      .then((data) => setTrips(data.trips || []))
      .catch(() => setTrips([]))
      .finally(() => setLoading(false));
  }, []);

  if (loading) {
    return (
      <div className="p-4 max-w-5xl mx-auto animate-fade-in">
        <h1 className="font-serif font-black text-2xl text-text-primary mb-4">
          我的行程
        </h1>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {[1, 2, 3].map((i) => (
            <TripCardSkeleton key={i} />
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="p-4 max-w-5xl mx-auto animate-fade-in">
      <h1 className="font-serif font-black text-2xl text-text-primary mb-4">
        我的行程
      </h1>

      {trips.length === 0 ? (
        <EmptyState
          icon="📋"
          title="还没有行程"
          description="点击下方按钮开始规划你的第一次旅行"
          actionLabel="✈️ 开始规划"
          onAction={() => navigate("/")}
        />
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {trips.map((trip, i) => {
            const allSpots = trip.itinerary_json
              ? Object.values(trip.itinerary_json).flat()
              : [];
            const spotCount = allSpots.length;

            return (
              <div
                key={trip.id}
                className="animate-fade-up"
                style={{ animationDelay: `${i * 80}ms` }}
              >
                <Card
                  hover
                  padding={false}
                  className="overflow-hidden h-full"
                  onClick={() => navigate(`/trips/${trip.id}`)}
                >
                {/* Hero 渐变区域 — Demo 三色渐变 */}
                <div
                  className="
                    relative h-[110px] overflow-hidden
                    flex items-center justify-center
                  "
                  style={{
                    background: "linear-gradient(135deg, #E8E0D5, #F0EAE0, #D5CFC6)",
                    opacity: 0.7,
                  }}
                >
                  <span className="text-[2.8rem] leading-none select-none">
                    {getCityEmoji(trip.city)}
                  </span>

                  {/* 状态标签 — 绝对定位右上角 */}
                  <div className="absolute top-2.5 right-2.5">
                    <Tag
                      variant={
                        trip.status === "confirmed" ? "teal" : "outline"
                      }
                    >
                      {trip.status === "draft" ? "草稿" : "已确认"}
                    </Tag>
                  </div>
                </div>

                {/* 卡片主体 */}
                <div className="p-[14px]">
                  <h3 className="text-[1.05rem] font-bold text-text-primary mb-0.5">
                    {trip.title}
                  </h3>

                  {/* 统计行：天数 / 景点数 / 创建日期 */}
                  <div className="flex gap-4 my-2">
                    <div className="text-center">
                      <div className="text-[1.1rem] font-bold text-text-primary">
                        {trip.days}
                      </div>
                      <div className="text-[0.62rem] text-ink-tertiary uppercase tracking-wider">
                        天数
                      </div>
                    </div>
                    <div className="text-center">
                      <div className="text-[1.1rem] font-bold text-text-primary">
                        {spotCount}
                      </div>
                      <div className="text-[0.62rem] text-ink-tertiary uppercase tracking-wider">
                        景点
                      </div>
                    </div>
                    <div className="text-center">
                      <div className="text-[1.1rem] font-bold text-text-primary">
                        {new Date(trip.created_at)
                          .getMonth() + 1}/{new Date(
                            trip.created_at,
                          ).getDate()}
                      </div>
                      <div className="text-[0.62rem] text-ink-tertiary uppercase tracking-wider">
                        日期
                      </div>
                    </div>
                  </div>

                  {/* 景点标签行 */}
                  {allSpots.length > 0 && (
                    <div className="flex flex-wrap gap-[5px] mt-2">
                      {allSpots.slice(0, 4).map((spot: unknown, j: number) => (
                        <span
                          key={j}
                          className="
                            px-[9px] py-[3px] rounded-[5px]
                            text-[0.7rem] font-medium
                            bg-sand text-ink-secondary
                          "
                        >
                          {typeof spot === "object" && spot !== null
                            ? (spot as Record<string, unknown>).name as string || `景点${j + 1}`
                            : `景点${j + 1}`}
                        </span>
                      ))}
                      {allSpots.length > 4 && (
                        <span className="text-[0.7rem] text-ink-tertiary self-center">
                          +{allSpots.length - 4}
                        </span>
                      )}
                    </div>
                  )}
                </div>
              </Card>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
