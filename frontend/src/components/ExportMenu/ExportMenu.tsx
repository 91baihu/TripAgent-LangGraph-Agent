/** 导出下拉菜单 — 支持复制纯文本 + 下载 MD/PDF/DOCX */

import { useState, useRef, useEffect } from "react";
import { Button } from "../Button/Button";
import { api } from "../../services/api";
import { endpoints } from "../../services/endpoints";
import { showToast } from "../Toast/ToastContainer";

interface ExportMenuProps {
  tripId: string;
}

interface ExportFormat {
  key: string;
  emoji: string;
  label: string;
  action: "copy" | "download";
}

const FORMATS: ExportFormat[] = [
  { key: "txt", emoji: "📋", label: "复制纯文本", action: "copy" },
  { key: "md", emoji: "📝", label: "下载 Markdown", action: "download" },
  { key: "docx", emoji: "📃", label: "下载 Word 文档", action: "download" },
  { key: "pdf", emoji: "📄", label: "下载 PDF", action: "download" },
];

export function ExportMenu({ tripId }: ExportMenuProps) {
  const [open, setOpen] = useState(false);
  const [loading, setLoading] = useState<string | null>(null);
  const menuRef = useRef<HTMLDivElement>(null);

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
        window.open(
          `${import.meta.env.VITE_API_BASE_URL || "/api/v1"}${endpoints.export.download(tripId, format.key)}`,
          "_blank"
        );
        showToast(`📥 正在下载 ${format.label}...`);
      }
      setOpen(false);
    } catch {
      showToast("导出失败，请稍后重试", "error");
    } finally {
      setLoading(null);
    }
  };

  return (
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
            absolute right-0 mt-2 w-[200px]
            bg-white shadow-lg rounded-card border border-divider
            py-1 z-50 animate-fade-up
          "
        >
          {FORMATS.map((f) => (
            <button
              key={f.key}
              onClick={() => handleAction(f)}
              disabled={loading === f.key}
              className="
                w-full text-left px-4 py-2.5 text-body text-text-primary
                hover:bg-sand transition-colors duration-150
                disabled:opacity-50
                flex items-center gap-2
              "
            >
              <span>{f.emoji}</span>
              <span>{f.label}</span>
              {loading === f.key && (
                <span className="ml-auto animate-spin">⏳</span>
              )}
            </button>
          ))}
        </div>
      )}
    </div>
  );
}
