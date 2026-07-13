/** QQ 极简风格输入框 */

import { InputHTMLAttributes, forwardRef } from "react";

interface InputProps extends InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  error?: string;
  prefix?: string;
}

export const Input = forwardRef<HTMLInputElement, InputProps>(
  ({ label, error, prefix, className = "", ...props }, ref) => {
    return (
      <div className="w-full">
        {label && (
          <label className="block mb-1 text-caption text-text-secondary">
            {label}
          </label>
        )}
        <div
          className={`
            flex items-center gap-2 h-[44px] px-4
            bg-sand rounded-input border-[1.5px]
            transition-all duration-200
            ${error
              ? "border-semantic-error focus-within:ring-2 focus-within:ring-semantic-error/15"
              : "border-warm-border hover:border-ink-tertiary/60 focus-within:border-teal focus-within:bg-white focus-within:ring-2 focus-within:ring-teal/15"
            }
          `}
        >
          {prefix && (
            <span className="text-text-tertiary text-body flex-shrink-0">
              {prefix}
            </span>
          )}
          <input
            ref={ref}
            className={`
              w-full bg-transparent text-body text-text-primary
              placeholder:text-text-tertiary outline-none
              ${className}
            `}
            {...props}
          />
        </div>
        {error && (
          <p className="mt-1 text-small text-semantic-error">{error}</p>
        )}
      </div>
    );
  }
);

Input.displayName = "Input";
