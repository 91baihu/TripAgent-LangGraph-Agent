/** 历史会话列表页 */

import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { Card } from "../../components/Card/Card";
import { EmptyState } from "../../components/EmptyState/EmptyState";
import { TripCardSkeleton } from "../../components/Skeleton/Skeleton";
import { api } from "../../services/api";
import { endpoints } from "../../services/endpoints";
import { showToast } from "../../components/Toast/ToastContainer";

interface Session {
  id: string;
  title: string;
  city: string | null;
  status: string;
  message_count: number;
  created_at: string;
  updated_at: string;
}

/** 城市 → emoji */
const cityEmoji: Record<string, string> = {
  北京: "🏯", 上海: "🌃", 杭州: "🛶", 成都: "🐼", 西安: "🏛️",
  重庆: "🌉", 厦门: "🏖️", 三亚: "🌴", 大理: "🏔️", 丽江: "🏘️",
  桂林: "⛰️", 苏州: "🌿", 青岛: "🍺", 南京: "🏯", 深圳: "🏙️",
  广州: "🌆", 武汉: "🌉", 长沙: "🏙️", 大连: "🌊", 哈尔滨: "❄️",
};

function getCityEmoji(city: string | null): string {
  return city ? cityEmoji[city] || "🗺️" : "💬";
}

function formatDate(isoStr: string): string {
  const d = new Date(isoStr);
  const now = new Date();
  const diffMs = now.getTime() - d.getTime();
  const diffMin = Math.floor(diffMs / 60000);
  const diffHour = Math.floor(diffMs / 3600000);

  if (diffMin < 1) return "刚刚";
  if (diffMin < 60) return `${diffMin} 分钟前`;
  if (diffHour < 24) return `${diffHour} 小时前`;
  return `${d.getMonth() + 1}/${d.getDate()}`;
}

export function SessionListPage() {
  const [sessions, setSessions] = useState<Session[]>([]);
  const [loading, setLoading] = useState(true);
  const [page, setPage] = useState(1);
  const [total, setTotal] = useState(0);
  const navigate = useNavigate();

  const fetchSessions = async (p: number) => {
    setLoading(true);
    try {
      const data = await api.get<{
        sessions: Session[];
        total: number;
        page: number;
        page_size: number;
      }>(`${endpoints.sessions.list}?page=${p}&page_size=20`);
      setSessions(data.sessions || []);
      setTotal(data.total || 0);
    } catch {
      showToast("加载历史会话失败", "error");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchSessions(page);
  }, [page]);

  const handleDelete = async (sessionId: string, e: React.MouseEvent) => {
    e.stopPropagation();
    if (!confirm("确定要删除此会话吗？")) return;
    try {
      await api.delete(endpoints.sessions.delete(sessionId));
      showToast("会话已删除");
      fetchSessions(page);
    } catch {
      showToast("删除失败", "error");
    }
  };

  if (loading) {
    return (
      <div className="min-h-dvh bg-surface-page animate-fade-in">
        <div className="max-w-2xl mx-auto p-4 space-y-4">
          <h1 className="font-serif font-black text-2xl text-text-primary">
            历史会话
          </h1>
          {[1, 2, 3].map((i) => (
            <TripCardSkeleton key={i} />
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-dvh bg-surface-page animate-fade-in">
      <div className="max-w-2xl mx-auto p-4">
        <h1 className="font-serif font-black text-2xl text-text-primary mb-4">
          历史会话
        </h1>

        {sessions.length === 0 ? (
          <EmptyState
            icon="💬"
            title="暂无历史会话"
            description="开始一次旅行规划对话，会话将自动保存"
            actionLabel="✈️ 开始规划"
            onAction={() => navigate("/")}
          />
        ) : (
          <div className="space-y-3">
            {sessions.map((session, i) => (
              <div
                key={session.id}
                className="animate-fade-up"
                style={{ animationDelay: `${i * 60}ms` }}
              >
                <Card
                  hover
                  padding
                  onClick={() => navigate(`/sessions/${session.id}`)}
                  className="cursor-pointer"
                >
                  <div className="flex items-center gap-3">
                    {/* 城市 emoji */}
                    <div className="w-10 h-10 rounded-xl bg-sand flex items-center justify-center text-xl flex-shrink-0">
                      {getCityEmoji(session.city)}
                    </div>

                    {/* 会话信息 */}
                    <div className="flex-1 min-w-0">
                      <h3 className="text-sm font-semibold text-text-primary truncate">
                        {session.title || "新的旅程"}
                      </h3>
                      <div className="flex items-center gap-2 mt-0.5">
                        {session.city && (
                          <span className="text-xs text-ink-tertiary">
                            📍 {session.city}
                          </span>
                        )}
                        <span className="text-xs text-ink-tertiary">
                          {formatDate(session.updated_at)}
                        </span>
                      </div>
                    </div>

                    {/* 删除按钮 */}
                    <button
                      onClick={(e) => handleDelete(session.id, e)}
                      className="
                        w-8 h-8 flex items-center justify-center
                        rounded-full text-ink-tertiary hover:text-rust hover:bg-rust-light
                        transition-colors bg-transparent border-none cursor-pointer flex-shrink-0
                      "
                      title="删除会话"
                    >
                      🗑️
                    </button>
                  </div>
                </Card>
              </div>
            ))}

            {/* 分页 */}
            {total > 20 && (
              <div className="flex justify-center gap-3 pt-4">
                <button
                  onClick={() => setPage(Math.max(1, page - 1))}
                  disabled={page <= 1}
                  className="
                    px-4 py-2 text-sm rounded-button
                    bg-white border border-warm-border
                    text-ink-secondary hover:text-ink
                    disabled:opacity-40 disabled:cursor-not-allowed
                    transition-colors cursor-pointer
                  "
                >
                  上一页
                </button>
                <span className="text-sm text-ink-tertiary self-center">
                  {page} / {Math.ceil(total / 20)}
                </span>
                <button
                  onClick={() => setPage(page + 1)}
                  disabled={page * 20 >= total}
                  className="
                    px-4 py-2 text-sm rounded-button
                    bg-white border border-warm-border
                    text-ink-secondary hover:text-ink
                    disabled:opacity-40 disabled:cursor-not-allowed
                    transition-colors cursor-pointer
                  "
                >
                  下一页
                </button>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
