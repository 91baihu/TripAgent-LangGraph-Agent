/** QQ 风格对话气泡 */

import { ReactNode } from "react";

type BubbleRole = "user" | "assistant";

interface BubbleProps {
  role: BubbleRole;
  children: ReactNode;
  className?: string;
}

export function Bubble({ role, children, className = "" }: BubbleProps) {
  const isUser = role === "user";

  return (
    <div
      className={`
        flex ${isUser ? "justify-end" : "justify-start"}
        mb-3 bubble-enter
      `}
    >
      <div
        className={`
          max-w-[80%] px-4 py-3 text-body leading-relaxed
          ${isUser
            ? "bg-primary text-text-inverse rounded-bubble rounded-br-md"
            : "bg-surface-card text-text-primary rounded-bubble rounded-bl-md border border-divider"
          }
          ${className}
        `}
      >
        {children}
      </div>
    </div>
  );
}

/** 思考中骨架气泡 */
export function ThinkingBubble() {
  return (
    <div className="flex justify-start mb-3">
      <div className="bg-surface-card border border-divider rounded-bubble rounded-bl-md px-5 py-4">
        <div className="flex gap-1.5">
          {[0, 1, 2].map((i) => (
            <span
              key={i}
              className="w-2 h-2 rounded-full bg-primary animate-bounce"
              style={{
                animationDelay: `${i * 0.15}s`,
                animationDuration: "0.8s",
              }}
            />
          ))}
        </div>
      </div>
    </div>
  );
}
