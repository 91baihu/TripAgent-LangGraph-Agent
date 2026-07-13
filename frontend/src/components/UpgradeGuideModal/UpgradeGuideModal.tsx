/** 升级引导弹窗 — 免费用戶点击导出时弹出 */

import { useEffect } from "react";
import { useNavigate } from "react-router-dom";

interface UpgradeGuideModalProps {
  open: boolean;
  onClose: () => void;
  featureName?: string;
}

export function UpgradeGuideModal({
  open,
  onClose,
  featureName = "文件导出",
}: UpgradeGuideModalProps) {
  const navigate = useNavigate();

  useEffect(() => {
    if (open) {
      document.body.style.overflow = "hidden";
    } else {
      document.body.style.overflow = "";
    }
    return () => {
      document.body.style.overflow = "";
    };
  }, [open]);

  if (!open) return null;

  return (
    <div className="fixed inset-0 z-[100] flex items-center justify-center p-4">
      {/* 遮罩 */}
      <div
        className="absolute inset-0 bg-black/40 animate-fade-in"
        onClick={onClose}
      />

      {/* 弹窗内容 */}
      <div
        className="
          relative w-full max-w-sm bg-white rounded-[20px]
          shadow-warm-lg animate-scale-in overflow-hidden
        "
      >
        {/* 顶部渐变 Hero */}
        <div
          className="
            relative h-[100px] flex items-center justify-center
            bg-gradient-to-br from-amber-100 via-orange-100 to-rose-100
          "
        >
          <span className="text-4xl">🌟</span>
          {/* 关闭按钮 */}
          <button
            onClick={onClose}
            className="
              absolute top-3 right-3 w-7 h-7 flex items-center justify-center
              rounded-full bg-white/60 backdrop-blur text-ink-tertiary
              hover:bg-white/90 transition-colors text-sm
              border-none cursor-pointer
            "
          >
            ✕
          </button>
        </div>

        {/* 内容 */}
        <div className="px-5 py-5">
          <h2 className="font-serif text-lg font-black text-text-primary mb-2">
            解锁 {featureName}
          </h2>
          <p className="text-sm text-ink-secondary leading-relaxed mb-4">
            {featureName} 是 <strong className="text-text-primary">TripAgent Pro</strong>{" "}
            会员专属功能。升级后即可解锁完整多格式导出（Word、PDF、Markdown）、优先队列和无限历史记录。
          </p>

          {/* 权益对比 */}
          <div className="bg-sand rounded-card p-3 mb-4 space-y-2">
            <div className="flex items-center gap-2 text-sm">
              <span className="text-rust">✕</span>
              <span className="text-ink-tertiary">免费版：仅支持一键复制文本</span>
            </div>
            <div className="flex items-center gap-2 text-sm">
              <span className="text-teal">✓</span>
              <span className="text-ink-secondary">Pro 版：全格式导出 + 优先队列</span>
            </div>
            <div className="flex items-center gap-2 text-sm">
              <span className="text-teal">✓</span>
              <span className="text-ink-secondary">无限历史记录 + 高清导出</span>
            </div>
          </div>

          {/* 操作按钮 */}
          <div className="flex gap-3">
            <button
              onClick={onClose}
              className="
                flex-1 h-[44px] rounded-button
                bg-sand-dark text-ink-secondary
                font-semibold text-sm
                hover:bg-sand-bg active:scale-[0.97]
                transition-all cursor-pointer border-none
              "
            >
              以后再说
            </button>
            <button
              onClick={() => {
                onClose();
                navigate("/pricing");
              }}
              className="
                flex-1 h-[44px] rounded-button
                bg-ink text-white
                font-semibold text-sm
                hover:bg-ink-secondary active:scale-[0.97]
                transition-all cursor-pointer border-none
              "
            >
              🚀 查看套餐
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
