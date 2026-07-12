/** 个人中心页 */

import { useNavigate } from "react-router-dom";
import { useAuthStore } from "../../stores/authStore";
import { showToast } from "../../components/Toast/ToastContainer";

export function MePage() {
  const { user, logout } = useAuthStore();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    showToast("已退出登录");
    navigate("/");
  };

  return (
    <div className="min-h-dvh bg-surface-page animate-fade-in">
      {/* Header */}
      <header
        className="
          flex-shrink-0 h-[52px] bg-white/85 backdrop-blur border-b border-warm-border2
          flex items-center px-4 sticky top-0 z-30
        "
      >
        <h1 className="font-serif text-lg font-black text-text-primary">
          TripAgent
        </h1>
      </header>

      <div className="p-4 space-y-4 max-w-lg mx-auto">
        {/* 用户信息卡片 */}
        <div className="flex flex-col items-center py-8">
          <div
            className="
              w-[72px] h-[72px] rounded-full bg-ink text-white
              flex items-center justify-center
              text-2xl font-bold mb-4 shadow-warm-md
            "
          >
            {user?.nickname?.[0] || user?.email?.[0]?.toUpperCase() || "我"}
          </div>
          <h2 className="font-serif text-xl font-bold text-text-primary mb-1">
            {user?.nickname || "旅行者"}
          </h2>
          <p className="text-sm text-ink-secondary">{user?.email}</p>
        </div>

        {/* 统计卡片 */}
        <div
          className="
            bg-white border border-warm-border2 rounded-card-lg
            p-4 grid grid-cols-3 gap-3 text-center
          "
        >
          <div className="flex flex-col items-center">
            <span className="text-2xl font-extrabold text-ink">—</span>
            <span className="text-[0.68rem] text-ink-tertiary mt-1">行程</span>
          </div>
          <div className="flex flex-col items-center">
            <span className="text-2xl font-extrabold text-ink">—</span>
            <span className="text-[0.68rem] text-ink-tertiary mt-1">城市</span>
          </div>
          <div className="flex flex-col items-center">
            <span className="text-2xl font-extrabold text-ink">—</span>
            <span className="text-[0.68rem] text-ink-tertiary mt-1">景点</span>
          </div>
        </div>

        {/* 偏好设置占位 */}
        <div className="bg-white border border-warm-border2 rounded-card-lg p-4">
          <h3 className="text-sm font-semibold text-ink mb-3">⚙️ 偏好设置</h3>
          <p className="text-caption text-ink-tertiary">预算偏好、出行方式等设置即将上线</p>
        </div>

        {/* 退出登录 */}
        <button
          onClick={handleLogout}
          className="
            w-full h-[44px] rounded-button
            bg-transparent border border-rust/30 text-rust
            font-semibold text-sm
            hover:bg-rust-light active:scale-[0.97]
            transition-all cursor-pointer
          "
        >
          🚪 退出登录
        </button>
      </div>
    </div>
  );
}
