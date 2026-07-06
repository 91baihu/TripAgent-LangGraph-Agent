/** QQ 风格胶囊标签 */

import { ReactNode } from "react";

type TagVariant = "default" | "primary" | "success" | "warning";

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
        inline-flex items-center px-3 h-7 text-caption font-medium
        rounded-tag transition-colors duration-150
        ${active ? styles.active : styles.base}
        ${onClick ? "cursor-pointer active:scale-95" : ""}
        ${className}
      `}
      onClick={onClick}
    >
      {children}
    </span>
  );
}
