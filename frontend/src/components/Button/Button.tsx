/** QQ 极简风格按钮 */

import { ButtonHTMLAttributes, ReactNode } from "react";

type ButtonVariant = "primary" | "secondary" | "danger" | "ghost" | "text";
type ButtonSize = "sm" | "md" | "lg";

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: ButtonVariant;
  size?: ButtonSize;
  loading?: boolean;
  icon?: ReactNode;
  children: ReactNode;
}

const variantClasses: Record<ButtonVariant, string> = {
  primary:
    "bg-text-primary text-text-inverse hover:bg-ink-secondary active:scale-[0.97]",
  secondary:
    "bg-transparent text-text-primary border-1.5 border-warm-border hover:border-text-primary active:scale-[0.97]",
  danger:
    "bg-rust text-white hover:opacity-90 active:scale-[0.97]",
  ghost:
    "bg-transparent text-ink-secondary hover:bg-sand-dark active:scale-[0.97]",
  text: "text-primary hover:bg-primary-light active:scale-[0.97]",
};

const sizeClasses: Record<ButtonSize, string> = {
  sm: "h-8 px-3 text-caption rounded-button",
  md: "h-[44px] px-5 text-body rounded-button",
  lg: "h-12 px-6 text-h3 rounded-button",
};

export function Button({
  variant = "primary",
  size = "md",
  loading = false,
  icon,
  children,
  disabled,
  className = "",
  ...props
}: ButtonProps) {
  return (
    <button
      className={`
        inline-flex items-center justify-center gap-2 font-medium
        transition-all duration-200 select-none
        disabled:opacity-40 disabled:cursor-not-allowed disabled:active:scale-100
        ${variantClasses[variant]}
        ${sizeClasses[size]}
        ${className}
      `}
      disabled={disabled || loading}
      {...props}
    >
      {loading ? (
        <Spinner />
      ) : icon ? (
        <span className="flex-shrink-0">{icon}</span>
      ) : null}
      {children}
    </button>
  );
}

/** 微型加载 Spinner — QQ 蓝圆环 */
function Spinner() {
  return (
    <svg
      className="animate-spin h-4 w-4"
      viewBox="0 0 24 24"
      fill="none"
    >
      <circle
        cx="12" cy="12" r="10"
        stroke="currentColor"
        strokeWidth="3"
        className="opacity-25"
      />
      <path
        d="M12 2a10 10 0 0 1 10 10"
        stroke="currentColor"
        strokeWidth="3"
        strokeLinecap="round"
      />
    </svg>
  );
}
