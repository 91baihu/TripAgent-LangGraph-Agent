/** 额度进度条 — 显示剩余额度/进度条/超额提示 */

import { useEffect } from "react";
import { useQuotaStore } from "../../stores/quotaStore";
import { useNavigate } from "react-router-dom";

const STATUS_COLORS = {
  normal: "bg-accent-green",
  warning: "bg-accent-orange",
  exhausted: "bg-accent-red",
} as const;

export function QuotaBar() {
  const { quota, fetchQuota } = useQuotaStore();
  const navigate = useNavigate();

  useEffect(() => {
    fetchQuota();
  }, [fetchQuota]);

  if (!quota) return null;

  const barColor = STATUS_COLORS[quota.status] || STATUS_COLORS.normal;

  return (
    <div className="px-4 py-2 bg-surface-card border-b border-divider">
      <div className="flex items-center justify-between text-xs text-ink-tertiary mb-1">
        <span>
          {quota.is_guest
            ? `🎁 游客 · 剩余 ${quota.remaining}/${quota.total} 次`
            : `💰 ${quota.plan_name} · 剩余 ${quota.remaining}/${quota.total} 次`}
        </span>
        {quota.status === "exhausted" && (
          <button
            onClick={() => navigate("/pricing")}
            className="text-accent-blue font-semibold hover:underline"
          >
            升级 →
          </button>
        )}
      </div>
      <div className="h-1.5 bg-surface-hover rounded-full overflow-hidden">
        <div
          className={`h-full rounded-full transition-all duration-500 ${barColor}`}
          style={{ width: `${Math.min(quota.percent, 100)}%` }}
        />
      </div>
      {quota.status === "exhausted" && !quota.is_guest && (
        <p className="text-[0.65rem] text-accent-orange mt-1">
          ⚠️ 额度已用尽，当前为体验模式。生成的计划无法保存和导出。
        </p>
      )}
      {quota.status === "exhausted" && quota.is_guest && (
        <p className="text-[0.65rem] text-accent-red mt-1">
          🚫 免费体验次数已用完，请注册登录后继续使用。
        </p>
      )}
    </div>
  );
}
