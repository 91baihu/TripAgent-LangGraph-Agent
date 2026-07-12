/** 行程详情页 */

import { useState, useEffect } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { Card } from "../../components/Card/Card";
import { Button } from "../../components/Button/Button";
import { Tag } from "../../components/Tag/Tag";
import { Skeleton } from "../../components/Skeleton/Skeleton";
import { Timeline, type TimelineSpot } from "../../components/Timeline/Timeline";
import { api } from "../../services/api";
import { endpoints } from "../../services/endpoints";
import { showToast } from "../../components/Toast/ToastContainer";

interface TripSpot {
  name: string;
  time: string;
  price: number;
  duration?: string;
  transport?: string;
  next_spot?: string;
  next_distance?: string;
}

interface Trip {
  id: string;
  title: string;
  city: string;
  days: number;
  itinerary_json: Record<string, TripSpot[]>;
  status: string;
  share_token?: string;
  created_at: string;
}

export function TripDetailPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [trip, setTrip] = useState<Trip | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!id) return;
    api
      .get<Trip>(endpoints.trips.get(id))
      .then(setTrip)
      .catch(() => navigate("/trips"))
      .finally(() => setLoading(false));
  }, [id, navigate]);

  const handleShare = async () => {
    if (!trip) return;
    try {
      const data = await api.post<{ share_url: string }>(
        endpoints.trips.share(trip.id)
      );
      await navigator.clipboard.writeText(data.share_url);
      showToast("分享链接已复制到剪贴板");
    } catch {
      showToast("分享失败，请稍后重试", "error");
    }
  };

  if (loading) {
    return (
      <div className="min-h-dvh bg-surface-page animate-fade-in">
        <div className="max-w-2xl mx-auto p-4 space-y-4">
          <Skeleton height={200} rounded="16px" />
          <Skeleton width="60%" height={24} />
          <Skeleton height={120} rounded="12px" />
          <Skeleton height={80} rounded="12px" />
        </div>
      </div>
    );
  }

  if (!trip) return null;

  const allSpots = Object.values(trip.itinerary_json).flat();
  const totalPrice = allSpots.reduce(
    (sum, s) => sum + (s.price || 0),
    0,
  );

  return (
    <div className="min-h-dvh bg-surface-page animate-fade-in">
      {/* 深色渐变 Hero — 桌面端更高 */}
      <header
        className="
          relative overflow-hidden flex-shrink-0
          bg-gradient-to-br from-ink to-ink-secondary
          flex flex-col justify-end p-[18px] text-white
          h-[200px] md:h-[260px]
        "
      >
        {/* 径向光晕叠加 */}
        <div
          className="
            absolute inset-0
            bg-[radial-gradient(circle_at_70%_30%,rgba(255,255,255,0.08)_0%,transparent_60%)]
          "
        />

        {/* 返回按钮 — 毛玻璃圆形 */}
        <button
          onClick={() => navigate(-1)}
          className="
            absolute top-[14px] left-[14px]
            w-[34px] h-[34px] rounded-full
            bg-white/12 backdrop-blur
            border-none text-white text-base
            cursor-pointer flex items-center justify-center
          "
        >
          ←
        </button>

        {/* 分享按钮 — 毛玻璃圆形 */}
        <button
          onClick={handleShare}
          className="
            absolute top-[14px] right-[14px]
            w-[34px] h-[34px] rounded-full
            bg-white/12 backdrop-blur
            border-none text-white text-base
            cursor-pointer flex items-center justify-center
          "
        >
          🔗
        </button>

        {/* 城市名 */}
        <h1 className="font-serif text-4xl font-black text-white relative">
          {trip.city}
        </h1>

        {/* Meta 标签行 */}
        <div className="flex gap-2 mt-1.5 relative">
          <span
            className="
              px-3 py-1 rounded-full text-[0.72rem] font-semibold
              bg-white/12 backdrop-blur
            "
          >
            {trip.days} 天行程
          </span>
          <span
            className="
              px-3 py-1 rounded-full text-[0.72rem] font-semibold
              bg-white/12 backdrop-blur
            "
          >
            {trip.status === "draft" ? "草稿" : "已确认"}
          </span>
        </div>
      </header>

      {/* 内容 — 桌面端居中限宽 */}
      <div className="max-w-2xl mx-auto p-4 space-y-4 md:space-y-6 md:py-6">
        {/* 概览统计网格 — 3列 */}
        <div
          className="
            bg-surface-card border border-divider rounded-card
            p-4 grid grid-cols-3 gap-2.5 text-center
            animate-fade-up
          "
        >
          <div className="flex flex-col items-center">
            <span className="text-xl font-bold text-text-primary">
              {trip.days}
            </span>
            <span className="text-[0.68rem] text-ink-tertiary mt-px">
              天数
            </span>
          </div>
          <div className="flex flex-col items-center">
            <span className="text-xl font-bold text-text-primary">
              {allSpots.length}
            </span>
            <span className="text-[0.68rem] text-ink-tertiary mt-px">
              景点
            </span>
          </div>
          <div className="flex flex-col items-center">
            <span className="text-xl font-bold text-text-primary">
              ¥{totalPrice}
            </span>
            <span className="text-[0.68rem] text-ink-tertiary mt-px">
              门票合计
            </span>
          </div>
        </div>

        {/* 每日行程 — 使用 Timeline 组件 */}
        {Object.entries(trip.itinerary_json).map(([dayKey, spots]) => {
          const timelineSpots: TimelineSpot[] = Array.isArray(spots)
            ? spots.map((spot) => ({
                time: spot.time,
                name: spot.name,
                duration: spot.duration || "2h",
                price: spot.price || 0,
                transport: spot.transport,
                nextSpot: spot.next_spot,
                nextDistance: spot.next_distance,
              }))
            : [];

          return (
            <Card key={dayKey} padding className="shadow-card">
              <Timeline
                dayLabel={dayKey}
                spots={timelineSpots}
              />
            </Card>
          );
        })}

        {/* 操作按钮 */}
        <div className="flex gap-3 pt-2 pb-6">
          <Button
            variant="secondary"
            className="flex-1"
            onClick={() => navigate(`/trips/${trip.id}/map`)}
          >
            🗺️ 地图查看
          </Button>
          <Button
            variant="primary"
            className="flex-1"
            onClick={handleShare}
          >
            🔗 分享行程
          </Button>
        </div>
      </div>
    </div>
  );
}
