/** QQ 风格 Toast */

import { useEffect, useState, useCallback, createContext, useContext } from "react";

type ToastType = "success" | "error" | "warning" | "info";

interface Toast {
  id: number;
  message: string;
  type: ToastType;
}

// ===== Toast Context =====
interface ToastContextValue {
  showToast: (message: string, type?: ToastType) => void;
}

const ToastContext = createContext<ToastContextValue>({
  showToast: () => {},
});

export const useToast = () => useContext(ToastContext);

// ===== Provider =====
let toastId = 0;
let globalShowToast: ((message: string, type?: ToastType) => void) | null = null;

/** 全局 showToast 方法（无需 hooks） */
export function showToast(message: string, type: ToastType = "info") {
  globalShowToast?.(message, type);
}

export function ToastProvider({ children }: { children: React.ReactNode }) {
  const [toasts, setToasts] = useState<Toast[]>([]);
  const [exitingIds, setExitingIds] = useState<Set<number>>(new Set());

  const show = useCallback((message: string, type: ToastType = "info") => {
    const id = ++toastId;
    setToasts((prev) => [...prev.slice(-4), { id, message, type }]);
    // 2s 后触发退出动画，2.2s 后移除 DOM
    setTimeout(() => {
      setExitingIds((prev) => new Set(prev).add(id));
    }, 2000);
    setTimeout(() => {
      setToasts((prev) => prev.filter((t) => t.id !== id));
      setExitingIds((prev) => {
        const next = new Set(prev);
        next.delete(id);
        return next;
      });
    }, 2200);
  }, []);

  useEffect(() => {
    globalShowToast = show;
    return () => {
      globalShowToast = null;
    };
  }, [show]);

  return (
    <ToastContext.Provider value={{ showToast: show }}>
      {children}
      <div className="fixed top-4 left-1/2 -translate-x-1/2 z-[100] flex flex-col gap-2 pointer-events-none">
        {toasts.map((toast) => (
          <div
            key={toast.id}
            className={`pointer-events-auto ${exitingIds.has(toast.id) ? "toast-exit" : "toast-enter"}`}
          >
            <ToastItem message={toast.message} type={toast.type} />
          </div>
        ))}
      </div>
    </ToastContext.Provider>
  );
}

// ===== Toast Item =====
const typeIcons: Record<ToastType, string> = {
  success: "✓",
  error: "✕",
  warning: "!",
  info: "i",
};

function ToastItem({ message, type }: { message: string; type: ToastType }) {
  return (
    <div className="flex items-center gap-2.5 bg-ink text-white rounded-full px-5 py-2.5 shadow-warm-md text-body font-medium max-w-[320px]">
      <span className="flex-shrink-0 w-5 h-5 rounded-full bg-white/15 flex items-center justify-center text-small font-bold">
        {typeIcons[type]}
      </span>
      <span className="truncate">{message}</span>
    </div>
  );
}

// 重新导出为默认容器
export { ToastProvider as ToastContainer };
