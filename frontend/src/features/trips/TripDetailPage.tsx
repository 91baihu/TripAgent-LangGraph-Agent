/** 行程详情页 */

import { useState, useEffect } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { Card } from "../../components/Card/Card";
import { Button } from "../../components/Button/Button";
import { Tag } from "../../components/Tag/Tag";
import { Skeleton } from "../../components/Skeleton/Skeleton";
import { api } from "../../services/api";
import { endpoints } from "../../services/endpoints";
import { showToast } from "../../components/Toast/ToastContainer";

interface Trip {
  id: string;
  title: string;
  city: string;
  days: number;
  itinerary_json: Record<string, Array<{ name: string; time: string; price: number }>>;
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
      <div className="p-4 space-y-3">
        <Skeleton width="60%" height={24} />
        <Skeleton height={120} />
        <Skeleton height={80} />
      </div>
    );
  }

  if (!trip) return null;

  return (
    <div className="min-h-dvh bg-surface-page">
      {/* 顶栏 */}
      <header
        className="
          sticky top-0 z-10 h-14 bg-surface-card border-b border-divider
          flex items-center gap-3 px-4
        "
      >
        <button
          onClick={() => navigate(-1)}
          className="w-8 h-8 flex items-center justify-center text-text-secondary hover:text-text-primary"
        >
          ←
        </button>
        <h1 className="text-h2 text-text-primary flex-1 truncate">
          {trip.title}
        </h1>
        <button
          onClick={handleShare}
          className="w-8 h-8 flex items-center justify-center text-primary"
        >
          🔗
        </button>
      </header>

      {/* 内容 */}
      <div className="p-4 space-y-4">
        {/* 概览卡片 */}
        <Card>
          <div className="flex items-center gap-3 mb-3">
            <span className="text-3xl">🏙️</span>
            <div>
              <p className="text-body text-text-secondary">目的地</p>
              <p className="text-h3 text-text-primary">{trip.city}</p>
            </div>
          </div>
          <div className="flex gap-3">
            <Tag>{trip.days}天行程</Tag>
            <Tag variant={trip.status === "confirmed" ? "success" : "default"}>
              {trip.status === "draft" ? "草稿" : "已确认"}
            </Tag>
          </div>
        </Card>

        {/* 每日行程 */}
        {Object.entries(trip.itinerary_json).map(([dayKey, spots]) => (
          <Card key={dayKey}>
            <h3 className="text-h3 text-text-primary mb-3">
              📅 {dayKey}
            </h3>
            <div className="space-y-2">
              {Array.isArray(spots) &&
                spots.map((spot, i) => (
                  <div
                    key={i}
                    className="flex items-start gap-3 p-3 bg-surface-page rounded-button"
                  >
                    <span className="w-6 h-6 rounded-full bg-primary text-text-inverse text-small flex items-center justify-center flex-shrink-0 mt-0.5">
                      {i + 1}
                    </span>
                    <div className="flex-1 min-w-0">
                      <p className="text-body text-text-primary font-medium">
                        {spot.name}
                      </p>
                      <p className="text-caption text-text-secondary">
                        {spot.time}
                        {spot.price > 0 && ` · ¥${spot.price}`}
                      </p>
                    </div>
                  </div>
                ))}
            </div>
          </Card>
        ))}

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
