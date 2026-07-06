/** QQ 风格底部导航栏 — 仅移动端显示 */

import { useLocation, useNavigate } from "react-router-dom";

interface NavItem {
  path: string;
  label: string;
  icon: string;
}

const navItems: NavItem[] = [
  { path: "/", label: "首页", icon: "🏠" },
  { path: "/trips", label: "行程", icon: "✈️" },
  { path: "/login", label: "登录", icon: "👤" },
];

export function BottomNav() {
  const location = useLocation();
  const navigate = useNavigate();

  const isActive = (path: string) => {
    if (path === "/") return location.pathname === "/";
    return location.pathname.startsWith(path);
  };

  return (
    <nav
      className="
        fixed bottom-0 left-0 right-0 z-50
        h-14 bg-surface-card border-t border-divider
        flex items-center justify-around
        safe-area-inset-bottom
      "
      style={{ paddingBottom: "env(safe-area-inset-bottom, 0px)" }}
    >
      {navItems.map((item) => {
        const active = isActive(item.path);
        return (
          <button
            key={item.path}
            onClick={() => navigate(item.path)}
            className={`
              flex flex-col items-center justify-center gap-0.5
              min-w-[64px] h-full transition-colors duration-150
              ${active ? "text-primary" : "text-text-tertiary"}
            `}
          >
            <span className="text-xl leading-none">{item.icon}</span>
            <span className="text-small leading-none">{item.label}</span>
          </button>
        );
      })}
    </nav>
  );
}
