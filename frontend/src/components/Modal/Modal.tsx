/** QQ 风格弹窗 */

import { ReactNode, useEffect } from "react";

interface ModalProps {
  open: boolean;
  onClose: () => void;
  title?: string;
  children: ReactNode;
  footer?: ReactNode;
}

export function Modal({ open, onClose, title, children, footer }: ModalProps) {
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
    <div className="fixed inset-0 z-[90] flex items-center justify-center p-4">
      {/* 遮罩 */}
      <div
        className="absolute inset-0 bg-black/40 animate-fadeIn"
        onClick={onClose}
      />

      {/* 弹窗内容 */}
      <div
        className="
          relative w-full max-w-sm bg-surface-card rounded-modal
          shadow-modal animate-bubbleIn overflow-hidden
        "
      >
        {title && (
          <div className="px-6 pt-6 pb-3">
            <h2 className="text-h2 text-text-primary">{title}</h2>
          </div>
        )}

        <div className="px-6 py-3">{children}</div>

        {footer && (
          <div className="px-6 pb-6 pt-3 flex gap-3 justify-end">
            {footer}
          </div>
        )}

        {/* 关闭按钮 */}
        {!footer && (
          <button
            onClick={onClose}
            className="
              absolute top-4 right-4 w-7 h-7 flex items-center justify-center
              rounded-full bg-surface-input text-text-secondary
              hover:bg-[#E0E1E3] transition-colors
            "
          >
            ✕
          </button>
        )}
      </div>
    </div>
  );
}
