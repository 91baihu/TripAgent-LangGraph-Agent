/** 检索进度条 — 细条 shimmer + 步骤描述动画 */

import { useChatStore } from "../../stores/chatStore";

export function SearchProgress() {
  const { progressPhase, progressPercent } = useChatStore();

  if (!progressPhase && progressPercent === 0) return null;

  return (
    <div className="flex-shrink-0 px-4 pb-2 card-enter">
      {/* 步骤描述 */}
      <div className="flex items-center justify-between mb-1">
        <span className="text-small text-text-secondary flex items-center gap-1.5">
          <span className="inline-block w-1.5 h-1.5 rounded-full bg-primary animate-pulse" />
          {progressPhase}
        </span>
        <span className="text-small text-text-tertiary tabular-nums">
          {progressPercent}%
        </span>
      </div>

      {/* 进度条 */}
      <div className="h-1 bg-surface-input rounded-full overflow-hidden">
        <div
          className="h-full rounded-full transition-all duration-500 ease-out"
          style={{
            width: `${progressPercent}%`,
            background:
              progressPercent < 100
                ? "linear-gradient(90deg, #12B7F5, #0E9FD6, #12B7F5)"
                : "#07C160",
            backgroundSize: progressPercent < 100 ? "200% 100%" : undefined,
            animation:
              progressPercent < 100
                ? "shimmer 2s ease-in-out infinite"
                : undefined,
          }}
        />
      </div>
    </div>
  );
}
