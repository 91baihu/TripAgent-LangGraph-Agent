/** QQ 风格骨架屏 */

interface SkeletonProps {
  width?: string | number;
  height?: string | number;
  rounded?: string;
  className?: string;
  count?: number;
}

export function Skeleton({
  width = "100%",
  height = 16,
  rounded = "6px",
  className = "",
  count = 1,
}: SkeletonProps) {
  return (
    <>
      {Array.from({ length: count }).map((_, i) => (
        <div
          key={i}
          className={`skeleton-shimmer ${className}`}
          style={{
            width: typeof width === "number" ? `${width}px` : width,
            height: typeof height === "number" ? `${height}px` : height,
            borderRadius: rounded,
            marginBottom: i < count - 1 ? "8px" : 0,
          }}
        />
      ))}
    </>
  );
}

/** 行程卡片骨架屏 — 对齐 Demo V3 卡片结构：Hero 渐变区 + 正文 */
export function TripCardSkeleton() {
  return (
    <div className="bg-surface-card rounded-card-lg border border-warm-border2 overflow-hidden">
      {/* Hero 骨架 — 对应 Demo .trip-card-hero 110px */}
      <div className="h-[110px] skeleton-shimmer opacity-70" />
      {/* 正文骨架 */}
      <div className="p-[14px] space-y-3">
        <Skeleton width="60%" height={20} />
        <Skeleton width="40%" height={14} />
        <div className="flex gap-2">
          <Skeleton width={80} height={28} rounded="100px" />
          <Skeleton width={80} height={28} rounded="100px" />
          <Skeleton width={80} height={28} rounded="100px" />
        </div>
      </div>
    </div>
  );
}

/** 对话消息骨架屏 */
export function ChatSkeleton() {
  return (
    <div className="space-y-3 p-4">
      {/* AI 消息 */}
      <div className="flex justify-start">
        <div className="bg-surface-card border border-divider rounded-bubble rounded-bl-md px-4 py-3 max-w-[80%] space-y-2">
          <Skeleton width={200} height={14} />
          <Skeleton width={160} height={14} />
        </div>
      </div>
      {/* 用户消息 */}
      <div className="flex justify-end">
        <div className="bg-primary rounded-bubble rounded-br-md px-4 py-3">
          <Skeleton width={120} height={14} className="bg-white/20" />
        </div>
      </div>
    </div>
  );
}
