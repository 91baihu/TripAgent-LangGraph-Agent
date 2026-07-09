/** QQ 极简风格卡片 */

import { ReactNode } from "react";

interface CardProps {
  children: ReactNode;
  className?: string;
  padding?: boolean;
  hover?: boolean;
  onClick?: () => void;
}

export function Card({
  children,
  className = "",
  padding = true,
  hover = false,
  onClick,
}: CardProps) {
  return (
    <div
      className={`
        bg-surface-card rounded-card border border-divider
        ${padding ? "p-4" : ""}
        ${hover ? "cursor-pointer transition-all duration-250 hover:shadow-warm-md hover:-translate-y-0.5 active:scale-[0.985]" : ""}
        ${onClick ? "cursor-pointer" : ""}
        ${className}
      `}
      onClick={onClick}
    >
      {children}
    </div>
  );
}

/** 可点击卡片 — 常用于列表项 */
export function ClickableCard({
  children,
  className = "",
  onClick,
}: {
  children: ReactNode;
  className?: string;
  onClick?: () => void;
}) {
  return (
    <Card hover padding className={className} onClick={onClick}>
      {children}
    </Card>
  );
}
