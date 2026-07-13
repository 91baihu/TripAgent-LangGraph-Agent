/** 导出下拉菜单 — 支持复制纯文本 + 下载 MD/PDF/DOCX
 *
 * 权限规则：
 * - 免费用户：仅可复制纯文本，文件格式被锁定（点击弹出升级引导）
 * - Pro/Admin：全部导出功能
 */

import { useState, useRef, useEffect } from "react";
import { Button } from "../Button/Button";
import { api } from "../../services/api";
import { endpoints } from "../../services/endpoints";
import { showToast } from "../Toast/ToastContainer";
import { useAuthStore } from "../../stores/authStore";
import { UpgradeGuideModal } from "../UpgradeGuideModal/UpgradeGuideModal";

interface ExportMenuProps {
  tripId: string;
}

interface ExportFormat {
  key: string;
  emoji: string;
  label: string;
  action: "copy" | "download";
  proOnly: boolean;
}

const FORMATS: ExportFormat[] = [
  { key: "txt", emoji: "📋", label: "复制纯文本", action: "copy", proOnly: false },
  { key: "md", emoji: "📝", label: "下载 Markdown", action: "download", proOnly: true },
  { key: "docx", emoji: "📃", label: "下载 Word 文档", action: "download", proOnly: true },
  { key: "pdf", emoji: "📄", label: "下载 PDF", action: "download", proOnly: true },
  { key: "html", emoji: "🌐", label: "下载 HTML", action: "download", proOnly: true },
];

export function ExportMenu({ tripId }: ExportMenuProps) {
  const [open, setOpen] = useState(false);
  const [loading, setLoading] = useState<string | null>(null);
  const [showUpgradeModal, setShowUpgradeModal] = useState(false);
  const menuRef = useRef<HTMLDivElement>(null);
  const { user } = useAuthStore();

  const isPro = user?.role === "pro" || user?.role === "family" || user?.role === "admin";

  // 点击外部关闭菜单
  useEffect(() => {
    if (!open) return;
    const handleClick = (e: MouseEvent) => {
      if (menuRef.current && !menuRef.current.contains(e.target as Node)) {
        setOpen(false);
      }
    };
    document.addEventListener("mousedown", handleClick);
    return () => document.removeEventListener("mousedown", handleClick);
  }, [open]);

  const handleAction = async (format: ExportFormat) => {
    // 非 Pro 用户点击 Pro 功能 → 弹出升级引导
    if (format.proOnly && !isPro) {
      setOpen(false);
      setShowUpgradeModal(true);
      return;
    }

    setLoading(format.key);
    try {
      if (format.action === "copy") {
        const data = await api.get<{ text: string }>(
          endpoints.export.text(tripId)
        );
        await navigator.clipboard.writeText(data.text);
        showToast("✅ 已复制到剪贴板");
      } else {
        // 触发浏览器下载
        const token = localStorage.getItem("access_token");
        const baseUrl = import.meta.env.VITE_API_BASE_URL || "/api/v1";
        const url = `${baseUrl}${endpoints.export.download(tripId, format.key)}`;

        // 使用 fetch + blob 下载（支持 Authorization header）
        const response = await fetch(url, {
          headers: { Authorization: `Bearer ${token || ""}` },
        });

        if (response.status === 402) {
          setOpen(false);
          setShowUpgradeModal(true);
          setLoading(null);
          return;
        }

        if (!response.ok) {
          throw new Error("下载失败");
        }

        const blob = await response.blob();
        const downloadUrl = URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = downloadUrl;
        a.download = `trip_${tripId}.${format.key}`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(downloadUrl);
        showToast(`📥 ${format.label} 下载完成`);
      }
      setOpen(false);
    } catch {
      showToast("操作失败，请稍后重试", "error");
    } finally {
      setLoading(null);
    }
  };

  return (
    <>
      <div ref={menuRef} className="relative inline-block">
        <Button
          variant="secondary"
          size="md"
          onClick={() => setOpen(!open)}
          disabled={loading !== null}
        >
          {loading ? "⏳" : "📥"} 导出
        </Button>

        {open && (
          <div
            className="
              absolute right-0 mt-2 w-[220px]
              bg-white shadow-warm-lg rounded-card-lg border border-warm-border2
              py-1 z-50 animate-scale-in origin-top-right
            "
          >
            {FORMATS.map((f) => {
              const isLocked = f.proOnly && !isPro;
              return (
                <button
                  key={f.key}
                  onClick={() => handleAction(f)}
                  disabled={loading === f.key}
                  className="
                    w-full text-left px-4 py-2.5 text-body
                    hover:bg-sand transition-colors duration-150
                    disabled:opacity-50
                    flex items-center gap-2
                    bg-transparent border-none cursor-pointer
                  "
                >
                  <span>{f.emoji}</span>
                  <span className={isLocked ? "text-ink-tertiary" : "text-text-primary"}>
                    {f.label}
                  </span>
                  {isLocked && (
                    <span className="ml-auto text-xs text-amber-500 font-medium">
                      🔒 Pro
                    </span>
                  )}
                  {loading === f.key && (
                    <span className="ml-auto animate-spin">⏳</span>
                  )}
                </button>
              );
            })}

            {/* 底部升级提示（仅免费用户可见） */}
            {!isPro && (
              <div className="border-t border-warm-border2 mt-1 pt-1 px-4 pb-2">
                <button
                  onClick={() => {
                    setOpen(false);
                    setShowUpgradeModal(true);
                  }}
                  className="
                    w-full text-center text-xs text-amber-600 hover:text-amber-700
                    font-medium py-1.5 transition-colors
                    bg-transparent border-none cursor-pointer
                  "
                >
                  🌟 升级 Pro 解锁全部导出格式 →
                </button>
              </div>
            )}
          </div>
        )}
      </div>

      {/* 升级引导弹窗 */}
      <UpgradeGuideModal
        open={showUpgradeModal}
        onClose={() => setShowUpgradeModal(false)}
        featureName="文件导出"
      />
    </>
  );
}
