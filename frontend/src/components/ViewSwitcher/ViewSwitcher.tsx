/** 移动端视图切换器 — Chat / Map / Rankings 三视图切换 */

export type MobileView = "chat" | "map" | "rankings" | "trace";

interface ViewItem {
  key: MobileView;
  label: string;
  icon: string;
}

const VIEWS: ViewItem[] = [
  { key: "chat", label: "对话", icon: "💬" },
  { key: "map", label: "地图", icon: "🗺️" },
  { key: "rankings", label: "排名", icon: "📊" },
];

interface ViewSwitcherProps {
  active: MobileView;
  onChange: (view: MobileView) => void;
  className?: string;
}

export function ViewSwitcher({ active, onChange, className = "" }: ViewSwitcherProps) {
  return (
    <div
      className={`
        flex-shrink-0 flex border-t border-divider bg-surface-card
        safe-area-inset-bottom
        ${className}
      `}
      style={{ paddingBottom: "env(safe-area-inset-bottom, 0px)" }}
    >
      {VIEWS.map((view) => (
        <button
          key={view.key}
          onClick={() => onChange(view.key)}
          className={`
            flex-1 flex flex-col items-center gap-0.5 py-2
            transition-colors duration-150
            ${active === view.key ? "text-text-primary" : "text-text-tertiary"}
          `}
        >
          <span className="text-lg leading-none">{view.icon}</span>
          <span className="text-small leading-none">{view.label}</span>
        </button>
      ))}
    </div>
  );
}
