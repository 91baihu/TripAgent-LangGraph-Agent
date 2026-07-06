/** QQ 风格空状态 */

import { ReactNode } from "react";
import { Button } from "../Button/Button";

interface EmptyStateProps {
  icon?: string;
  title: string;
  description?: string;
  actionLabel?: string;
  onAction?: () => void;
  children?: ReactNode;
}

export function EmptyState({
  icon = "📋",
  title,
  description,
  actionLabel,
  onAction,
  children,
}: EmptyStateProps) {
  return (
    <div className="flex flex-col items-center justify-center py-12 px-6 text-center">
      <span className="text-5xl mb-5 opacity-80">{icon}</span>
      <h3 className="text-h3 text-text-primary mb-2">{title}</h3>
      {description && (
        <p className="text-body text-text-secondary mb-6 max-w-[280px] leading-relaxed">
          {description}
        </p>
      )}
      {actionLabel && onAction && (
        <Button onClick={onAction} size="md">
          {actionLabel}
        </Button>
      )}
      {children}
    </div>
  );
}

/** 虚线边框空状态 — 行程占位 */
export function DashedEmptyState({
  children,
  className = "",
}: {
  children: ReactNode;
  className?: string;
}) {
  return (
    <div
      className={`
        border-2 border-dashed border-divider rounded-card-lg
        flex items-center justify-center p-8
        ${className}
      `}
    >
      {children}
    </div>
  );
}
