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
      <div className="p-4 space-y-3">
        <h1 className="text-h2 text-text-primary mb-4">我的行程</h1>
        {[1, 2, 3].map((i) => (
          <TripCardSkeleton key={i} />
        ))}
      </div>
    );
  }

  return (
    <div className="p-4">
      <h1 className="text-h2 text-text-primary mb-4">我的行程</h1>

      {trips.length === 0 ? (
        <EmptyState
          icon="📋"
          title="还没有行程"
          description="点击下方按钮开始规划你的第一次旅行"
          actionLabel="✈️ 开始规划"
          onAction={() => navigate("/")}
        />
      ) : (
        <div className="space-y-3">
          {trips.map((trip) => (
            <Card
              key={trip.id}
              hover
              padding
              onClick={() => navigate(`/trips/${trip.id}`)}
            >
              <div className="flex items-start justify-between mb-2">
                <div>
                  <h3 className="text-h3 text-text-primary">
                    🏙️ {trip.title}
                  </h3>
                  <p className="text-caption text-text-secondary mt-1">
                    {trip.city} · {trip.days}天
                  </p>
                </div>
                <Tag
                  variant={
                    trip.status === "confirmed" ? "success" : "default"
                  }
                  active={trip.status === "confirmed"}
                >
                  {trip.status === "draft" ? "草稿" : "已确认"}
                </Tag>
              </div>

              {/* 景点预览 */}
              {trip.itinerary_json &&
                Object.values(trip.itinerary_json).length > 0 && (
                  <div className="flex flex-wrap gap-1.5 mt-2">
                    {Object.values(trip.itinerary_json)
                      .flat()
                      .slice(0, 4)
                      .map((spot: unknown, i: number) => (
                        <span
                          key={i}
                          className="text-small text-text-secondary bg-surface-input px-2 py-0.5 rounded-tag"
                        >
                          {typeof spot === "object" && spot !== null
                            ? (spot as Record<string, unknown>).name as string || `景点${i + 1}`
                            : `景点${i + 1}`}
                        </span>
                      ))}
                    {Object.values(trip.itinerary_json).flat().length > 4 && (
                      <span className="text-small text-text-tertiary">
                        +{Object.values(trip.itinerary_json).flat().length - 4}
                      </span>
                    )}
                  </div>
                )}

              {/* 底部时间 */}
              <p className="text-small text-text-tertiary mt-3">
                {new Date(trip.created_at).toLocaleDateString("zh-CN")}
              </p>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
