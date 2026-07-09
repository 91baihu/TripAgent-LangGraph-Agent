/** QQ 风格胶囊标签 */

import { ReactNode } from "react";

type TagVariant = "default" | "primary" | "success" | "warning" | "teal" | "rust" | "outline" | "fill";

interface TagProps {
  children: ReactNode;
  variant?: TagVariant;
  active?: boolean;
  onClick?: () => void;
  className?: string;
}

const variantClasses: Record<TagVariant, { base: string; active: string }> = {
  default: {
    base: "bg-surface-input text-text-secondary",
    active: "bg-text-primary text-text-inverse",
  },
  primary: {
    base: "bg-primary-light text-primary",
    active: "bg-primary text-text-inverse",
  },
  success: {
    base: "bg-[#E8F8EF] text-semantic-success",
    active: "bg-semantic-success text-text-inverse",
  },
  warning: {
    base: "bg-[#FFF4EB] text-semantic-warning",
    active: "bg-semantic-warning text-text-inverse",
  },
  // 🆕 Demo V3 新增变体
  teal: {
    base: "bg-teal-light text-teal-dark",
    active: "bg-teal text-white",
  },
  rust: {
    base: "bg-rust-light text-rust",
    active: "bg-rust text-white",
  },
  outline: {
    base: "bg-transparent border border-warm-border text-ink-secondary",
    active: "bg-text-primary text-white border-text-primary",
  },
  fill: {
    base: "bg-sand-dark text-text-primary",
    active: "bg-text-primary text-white",
  },
};

export function Tag({
  children,
  variant = "default",
  active = false,
  onClick,
  className = "",
}: TagProps) {
  const styles = variantClasses[variant];

  return (
    <span
      className={`
        inline-flex items-center gap-1 px-3 h-7 text-caption font-medium
        rounded-tag transition-all duration-200
        ${active ? styles.active : styles.base}
        ${onClick ? "cursor-pointer active:scale-95 hover:shadow-warm-sm" : ""}
        ${className}
      `}
      onClick={onClick}
    >
      {children}
    </span>
  );
}
