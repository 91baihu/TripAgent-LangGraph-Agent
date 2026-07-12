/** 管理员面板 — Dashboard + 用户管理 + 系统统计 */

import { useEffect, useState, useCallback } from "react";
import { useAuthStore } from "../../stores/authStore";
import { api } from "../../services/api";
import { showToast } from "../../components/Toast/ToastContainer";

interface DashboardStats {
  users: { total: number; paid: number; admin: number; today_new: number };
  content: { total_trips: number; total_sessions: number };
  revenue: { total_orders: number; paid_orders: number; total_revenue_cents: number; total_revenue_display: string };
  devices: number;
}

interface UserItem {
  id: string; email: string; nickname: string; role: string;
  is_active: boolean; credits_balance: number; monthly_quota: number; created_at: string | null;
}

type TabId = "dashboard" | "users";

const TAB_LABELS: Record<TabId, string> = {
  dashboard: "📊 仪表盘",
  users: "👥 用户管理",
};

const ROLE_LABELS: Record<string, string> = {
  admin: "管理员",
  pro: "Pro",
  family: "家庭",
  free: "免费",
};

const ROLE_COLORS: Record<string, string> = {
  admin: "bg-red-100 text-red-700",
  pro: "bg-blue-100 text-blue-700",
  family: "bg-green-100 text-green-700",
  free: "bg-ink-tertiary/10 text-ink-secondary",
};

export function AdminPage() {
  const { user } = useAuthStore();

  const [activeTab, setActiveTab] = useState<TabId>("dashboard");
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [users, setUsers] = useState<UserItem[]>([]);
  const [userTotal, setUserTotal] = useState(0);
  const [userPage, setUserPage] = useState(1);
  const [userRoleFilter, setUserRoleFilter] = useState("");
  const [loading, setLoading] = useState(false);
  const [promoting, setPromoting] = useState(false);

  // ===== 加载仪表盘 =====
  const loadStats = useCallback(async () => {
    setLoading(true);
    try {
      const data = await api.get<DashboardStats>("/admin/stats");
      setStats(data);
    } catch (e: any) {
      showToast(e?.message || "加载统计数据失败", "error");
    } finally {
      setLoading(false);
    }
  }, []);

  // ===== 加载用户列表 =====
  const loadUsers = useCallback(async (page = 1, role = "") => {
    setLoading(true);
    try {
      const params = new URLSearchParams();
      params.set("page", String(page));
      params.set("page_size", "50");
      if (role) params.set("role", role);

      const data = await api.get<{ total: number; items: UserItem[] }>(
        `/admin/users?${params.toString()}`
      );
      setUsers(data.items);
      setUserTotal(data.total);
      setUserPage(page);
      setUserRoleFilter(role);
    } catch (e: any) {
      showToast(e?.message || "加载用户列表失败", "error");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    if (activeTab === "dashboard") loadStats();
    else if (activeTab === "users") loadUsers();
  }, [activeTab, loadStats, loadUsers]);

  // ===== 提升用户角色 =====
  const handlePromote = async (userId: string, role: string) => {
    setPromoting(true);
    try {
      await api.post(`/admin/users/${userId}/promote`, {
        user_id: userId,
        role,
      });
      showToast(`用户角色已更新为 ${ROLE_LABELS[role] || role}`);
      loadUsers(userPage, userRoleFilter);
    } catch (e: any) {
      showToast(e?.message || "操作失败", "error");
    } finally {
      setPromoting(false);
    }
  };

  // ===== 赠送额度 =====
  const handleGrantCredits = async (userId: string) => {
    const amount = prompt("赠送额度数量（上限100000）:", "100");
    if (!amount) return;
    try {
      await api.post(`/admin/users/${userId}/grant-credits`, {
        user_id: userId,
        amount: parseInt(amount, 10),
        description: "管理员手动赠送",
      });
      showToast(`已赠送 ${amount} 次额度`);
      loadUsers(userPage, userRoleFilter);
    } catch (e: any) {
      showToast(e?.message || "操作失败", "error");
    }
  };

  // ===== 一键提升自己为管理员（开发环境） =====
  const handleSelfPromote = async () => {
    setPromoting(true);
    try {
      const result = await api.post<{ message: string; role: string }>("/admin/self-promote");
      showToast(result.message || "已提升为管理员");
      // 刷新页面以更新 store
      window.location.reload();
    } catch (e: any) {
      showToast(e?.message || "提升失败", "error");
    } finally {
      setPromoting(false);
    }
  };

  // ===== 如果当前用户不是管理员，显示提升入口 =====
  if (user?.role !== "admin") {
    return (
      <div className="min-h-dvh bg-surface-page flex items-center justify-center p-4">
        <div className="max-w-md w-full text-center space-y-6">
          <div className="text-6xl">🔒</div>
          <h1 className="font-serif text-2xl font-black text-text-primary">管理员面板</h1>
          <p className="text-ink-secondary">
            当前角色：<strong>{ROLE_LABELS[user?.role || "free"] || "用户"}</strong>，需要管理员权限才能访问。
          </p>
          <button
            onClick={handleSelfPromote}
            disabled={promoting}
            className="
              px-8 py-3 bg-ink text-white rounded-button font-semibold
              hover:bg-ink/85 active:scale-[0.97] transition-all
              disabled:opacity-50 cursor-pointer
            "
          >
            {promoting ? "⏳ 处理中..." : "⚡ 一键提升为管理员 (开发模式)"}
          </button>
          <p className="text-xs text-ink-tertiary">
            该功能仅在开发环境（APP_ENV=dev）下可用
          </p>
        </div>
      </div>
    );
  }

  // ===== 管理员视图 =====
  return (
    <div className="min-h-dvh bg-surface-page animate-fade-in">
      {/* Header */}
      <header
        className="
          flex-shrink-0 h-[52px] bg-white/85 backdrop-blur border-b border-warm-border2
          flex items-center px-4 sticky top-0 z-30
        "
      >
        <h1 className="font-serif text-lg font-black text-text-primary">管理员面板</h1>
        <span className="ml-3 px-2 py-0.5 bg-red-100 text-red-600 text-xs font-bold rounded">
          ADMIN
        </span>
      </header>

      {/* Tabs */}
      <div className="flex border-b border-warm-border2 bg-white px-2">
        {(Object.keys(TAB_LABELS) as TabId[]).map((tab) => (
          <button
            key={tab}
            onClick={() => setActiveTab(tab)}
            className={`
              px-4 py-2.5 text-sm font-semibold transition-all cursor-pointer
              border-b-2 -mb-[1px]
              ${activeTab === tab
                ? "border-ink text-ink"
                : "border-transparent text-ink-secondary hover:text-ink"
              }
            `}
          >
            {TAB_LABELS[tab]}
          </button>
        ))}
      </div>

      {/* Content */}
      <div className="p-4 max-w-5xl mx-auto">
        {loading && (
          <div className="text-center py-12 text-ink-secondary">加载中...</div>
        )}

        {/* ===== 仪表盘 ===== */}
        {!loading && activeTab === "dashboard" && stats && (
          <div className="space-y-6">
            {/* 统计卡片 */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
              <StatCard label="用户总数" value={stats.users.total} sub={`今日新增 ${stats.users.today_new}`} />
              <StatCard label="付费用户" value={stats.users.paid} sub={`管理员 ${stats.users.admin}`} />
              <StatCard label="行程总数" value={stats.content.total_trips} sub={`会话 ${stats.content.total_sessions}`} />
              <StatCard label="营收" value={stats.revenue.total_revenue_display} sub={`${stats.revenue.paid_orders} 笔已付`} />
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {/* 快捷操作 */}
              <div className="bg-white border border-warm-border2 rounded-card-lg p-4">
                <h2 className="font-bold text-ink mb-3">⚡ 快捷操作</h2>
                <div className="space-y-2">
                  <button
                    onClick={() => setActiveTab("users")}
                    className="w-full text-left px-3 py-2 rounded-button bg-ink-secondary/5 hover:bg-ink-secondary/10 text-sm transition-all cursor-pointer"
                  >
                    👥 管理用户 → 查看/提升/赠送额度
                  </button>
                  <button
                    onClick={loadStats}
                    className="w-full text-left px-3 py-2 rounded-button bg-ink-secondary/5 hover:bg-ink-secondary/10 text-sm transition-all cursor-pointer"
                  >
                    🔄 刷新统计数据
                  </button>
                </div>
              </div>

              {/* 营收概览 */}
              <div className="bg-white border border-warm-border2 rounded-card-lg p-4">
                <h2 className="font-bold text-ink mb-3">💰 营收概览</h2>
                <div className="space-y-2 text-sm">
                  <div className="flex justify-between">
                    <span className="text-ink-secondary">总订单</span>
                    <span className="font-bold">{stats.revenue.total_orders}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-ink-secondary">已支付</span>
                    <span className="font-bold text-green-600">{stats.revenue.paid_orders}</span>
                  </div>
                  <div className="flex justify-between border-t border-warm-border2 pt-2">
                    <span className="text-ink-secondary">总收入</span>
                    <span className="font-bold text-lg">{stats.revenue.total_revenue_display}</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* ===== 用户管理 ===== */}
        {!loading && activeTab === "users" && (
          <div className="space-y-4">
            {/* 筛选栏 */}
            <div className="flex gap-2 flex-wrap">
              {["", "free", "pro", "family", "admin"].map((role) => (
                <button
                  key={role}
                  onClick={() => loadUsers(1, role)}
                  className={`
                    px-3 py-1.5 rounded-button text-xs font-semibold transition-all cursor-pointer
                    ${userRoleFilter === role
                      ? "bg-ink text-white"
                      : "bg-ink-secondary/5 text-ink-secondary hover:bg-ink-secondary/10"
                    }
                  `}
                >
                  {role ? ROLE_LABELS[role] : "全部"}
                </button>
              ))}
              <span className="ml-auto text-xs text-ink-tertiary self-center">
                共 {userTotal} 人
              </span>
            </div>

            {/* 用户列表 */}
            <div className="bg-white border border-warm-border2 rounded-card-lg overflow-hidden">
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b border-warm-border2 bg-ink-secondary/3">
                      <th className="text-left px-4 py-2.5 text-xs font-semibold text-ink-secondary">用户</th>
                      <th className="text-left px-4 py-2.5 text-xs font-semibold text-ink-secondary">角色</th>
                      <th className="text-right px-4 py-2.5 text-xs font-semibold text-ink-secondary">额度</th>
                      <th className="text-center px-4 py-2.5 text-xs font-semibold text-ink-secondary">状态</th>
                      <th className="text-right px-4 py-2.5 text-xs font-semibold text-ink-secondary">操作</th>
                    </tr>
                  </thead>
                  <tbody>
                    {users.map((u) => (
                      <tr key={u.id} className="border-b border-warm-border2/50 hover:bg-ink-secondary/3">
                        <td className="px-4 py-3">
                          <div className="font-semibold text-ink">{u.nickname || "未命名"}</div>
                          <div className="text-xs text-ink-tertiary">{u.email}</div>
                        </td>
                        <td className="px-4 py-3">
                          <span className={`px-2 py-0.5 rounded text-xs font-bold ${ROLE_COLORS[u.role] || ""}`}>
                            {ROLE_LABELS[u.role] || u.role}
                          </span>
                        </td>
                        <td className="px-4 py-3 text-right font-mono text-xs">
                          <span className={u.credits_balance > 0 ? "text-ink" : "text-rust"}>
                            {u.credits_balance}
                          </span>
                          <span className="text-ink-tertiary"> / {u.monthly_quota}</span>
                        </td>
                        <td className="px-4 py-3 text-center">
                          {u.is_active ? (
                            <span className="text-green-600 text-xs font-bold">正常</span>
                          ) : (
                            <span className="text-rust text-xs font-bold">禁用</span>
                          )}
                        </td>
                        <td className="px-4 py-3 text-right">
                          <div className="flex gap-1 justify-end">
                            {/* 角色提升下拉 */}
                            {u.role !== "admin" && (
                              <select
                                value=""
                                onChange={(e) => {
                                  if (e.target.value) handlePromote(u.id, e.target.value);
                                }}
                                disabled={promoting}
                                className="
                                  text-xs border border-warm-border2 rounded px-2 py-1
                                  bg-white cursor-pointer
                                "
                              >
                                <option value="">设为...</option>
                                <option value="free">免费版</option>
                                <option value="pro">Pro</option>
                                <option value="family">家庭版</option>
                                <option value="admin">管理员</option>
                              </select>
                            )}
                            <button
                              onClick={() => handleGrantCredits(u.id)}
                              disabled={promoting}
                              className="
                                text-xs px-2 py-1 rounded bg-ink-secondary/5
                                hover:bg-ink-secondary/10 transition-all cursor-pointer
                                text-ink-secondary
                              "
                            >
                              🎁 赠额度
                            </button>
                          </div>
                        </td>
                      </tr>
                    ))}
                    {users.length === 0 && (
                      <tr>
                        <td colSpan={5} className="px-4 py-12 text-center text-ink-tertiary">
                          暂无用户数据
                        </td>
                      </tr>
                    )}
                  </tbody>
                </table>
              </div>
            </div>

            {/* 分页 */}
            {userTotal > 50 && (
              <div className="flex justify-center gap-2">
                <button
                  onClick={() => loadUsers(userPage - 1, userRoleFilter)}
                  disabled={userPage <= 1}
                  className="px-4 py-2 rounded-button text-sm border border-warm-border2 disabled:opacity-30 cursor-pointer"
                >
                  上一页
                </button>
                <span className="px-4 py-2 text-sm text-ink-secondary">
                  {userPage} / {Math.ceil(userTotal / 50)}
                </span>
                <button
                  onClick={() => loadUsers(userPage + 1, userRoleFilter)}
                  disabled={userPage >= Math.ceil(userTotal / 50)}
                  className="px-4 py-2 rounded-button text-sm border border-warm-border2 disabled:opacity-30 cursor-pointer"
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

/** 仪表盘统计卡片 */
function StatCard({ label, value, sub }: { label: string; value: string | number; sub?: string }) {
  return (
    <div className="bg-white border border-warm-border2 rounded-card-lg p-4">
      <div className="text-xs text-ink-tertiary mb-1">{label}</div>
      <div className="text-2xl font-extrabold text-ink">{value}</div>
      {sub && <div className="text-xs text-ink-tertiary mt-1">{sub}</div>}
    </div>
  );
}
