/** Header 用户菜单 — 未登录显示登录按钮，已登录显示头像下拉 */

import { useState, useRef, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { useAuthStore } from "../../stores/authStore";
import { showToast } from "../Toast/ToastContainer";

export function UserMenu() {
  const { user, isAuthenticated, logout } = useAuthStore();
  const navigate = useNavigate();
  const [open, setOpen] = useState(false);
  const menuRef = useRef<HTMLDivElement>(null);

  // 点击外部关闭
  useEffect(() => {
    const handler = (e: MouseEvent) => {
      if (menuRef.current && !menuRef.current.contains(e.target as Node)) {
        setOpen(false);
      }
    };
    if (open) {
      document.addEventListener("mousedown", handler);
    }
    return () => document.removeEventListener("mousedown", handler);
  }, [open]);

  const handleLogout = () => {
    logout();
    setOpen(false);
    showToast("已退出登录");
    navigate("/");
  };

  if (!isAuthenticated) {
    return (
      <button
        onClick={() => navigate("/login")}
        className="
          text-sm font-semibold text-ink-secondary hover:text-ink
          transition-colors bg-transparent border-none cursor-pointer
          px-0
        "
      >
        登录
      </button>
    );
  }

  const initial = user?.nickname?.[0] || user?.email?.[0]?.toUpperCase() || "我";

  return (
    <div ref={menuRef} className="relative">
      <button
        onClick={() => setOpen(!open)}
        className="
          w-[30px] h-[30px] rounded-full bg-ink text-white
          flex items-center justify-center
          text-[11px] font-bold border-none cursor-pointer
          hover:bg-ink-secondary transition-colors
        "
      >
        {initial}
      </button>

      {open && (
        <div
          className="
            absolute right-0 top-full mt-2 w-52
            bg-white border border-warm-border rounded-xl
            shadow-warm-lg overflow-hidden z-50
            animate-scale-in origin-top-right
          "
        >
          {/* 用户信息 */}
          <div className="px-4 pt-4 pb-3 border-b border-warm-border2">
            <div className="flex items-center gap-3">
              <div className="w-9 h-9 rounded-full bg-ink text-white flex items-center justify-center text-xs font-bold flex-shrink-0">
                {initial}
              </div>
              <div className="min-w-0">
                <p className="text-sm font-semibold text-ink truncate">
                  {user?.nickname || "旅行者"}
                </p>
                <p className="text-[0.7rem] text-ink-tertiary truncate">
                  {user?.email || ""}
                </p>
              </div>
            </div>
          </div>

          {/* 菜单项 */}
          <div className="py-1">
            <button
              onClick={() => {
                setOpen(false);
                navigate("/trips");
              }}
              className="
                w-full flex items-center gap-3 px-4 py-2.5
                text-sm text-ink-secondary hover:bg-sand hover:text-ink
                transition-colors bg-transparent border-none cursor-pointer text-left
              "
            >
              <span>📋</span> 我的行程
            </button>
            <button
              onClick={() => {
                setOpen(false);
                navigate("/me");
              }}
              className="
                w-full flex items-center gap-3 px-4 py-2.5
                text-sm text-ink-secondary hover:bg-sand hover:text-ink
                transition-colors bg-transparent border-none cursor-pointer text-left
              "
            >
              <span>⚙️</span> 设置
            </button>
          </div>

          {/* 退出 */}
          <div className="border-t border-warm-border2 py-1">
            <button
              onClick={handleLogout}
              className="
                w-full flex items-center gap-3 px-4 py-2.5
                text-sm text-rust hover:bg-rust-light
                transition-colors bg-transparent border-none cursor-pointer text-left
              "
            >
              <span>🚪</span> 退出登录
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
