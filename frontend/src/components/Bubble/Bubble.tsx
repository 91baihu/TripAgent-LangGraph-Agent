/** QQ 风格对话气泡 — 带头像 */

import { ReactNode } from "react";

/** 简易 Markdown 渲染 — 将纯文本转为带样式的 React 节点 */
function renderMarkdown(text: string): ReactNode {
  if (!text) return null;

  const lines = text.split("\n");
  const elements: ReactNode[] = [];

  let inTable = false;
  let tableRows: string[][] = [];
  let tableHeader: string[] = [];

  for (let i = 0; i < lines.length; i++) {
    const line = lines[i];

    // 空行
    if (!line.trim()) {
      if (inTable) {
        // 结束表格
        elements.push(renderTable(tableHeader, tableRows));
        inTable = false;
        tableRows = [];
        tableHeader = [];
      }
      elements.push(<div key={`br-${i}`} className="h-3" />);
      continue;
    }

    // 表格行
    if (line.includes("|") && line.trim().startsWith("|")) {
      const cells = line.split("|").filter(c => c.trim() !== "").map(c => c.trim());
      if (cells.length === 0) continue;
      // 判断是否是分隔行
      if (cells.every(c => /^[-:]+$/.test(c))) continue;
      if (!inTable) {
        inTable = true;
        tableHeader = cells;
      } else {
        tableRows.push(cells);
      }
      continue;
    } else if (inTable) {
      elements.push(renderTable(tableHeader, tableRows));
      inTable = false;
      tableRows = [];
      tableHeader = [];
    }

    // 标题
    if (line.startsWith("### ")) {
      elements.push(
        <h4 key={`h4-${i}`} className="text-h4 text-text-primary font-semibold mt-3 mb-1">
          {renderInlineMarkdown(line.slice(4))}
        </h4>
      );
      continue;
    }
    if (line.startsWith("## ")) {
      elements.push(
        <h3 key={`h3-${i}`} className="text-h3 text-text-primary font-bold mt-4 mb-2">
          {renderInlineMarkdown(line.slice(3))}
        </h3>
      );
      continue;
    }

    // 列表项
    if (/^\d+\.\s/.test(line)) {
      elements.push(
        <li key={`li-${i}`} className="text-body text-text-secondary ml-4 list-decimal">
          <span>{renderInlineMarkdown(line.replace(/^\d+\.\s/, ""))}</span>
        </li>
      );
      continue;
    }
    if (/^[-*]\s/.test(line)) {
      elements.push(
        <li key={`li-${i}`} className="text-body text-text-secondary ml-4 list-disc">
          <span>{renderInlineMarkdown(line.replace(/^[-*]\s/, ""))}</span>
        </li>
      );
      continue;
    }

    // 普通段落
    elements.push(
      <p key={`p-${i}`} className="text-body text-text-secondary leading-relaxed">
        {renderInlineMarkdown(line)}
      </p>
    );
  }

  // 残留表格
  if (inTable) {
    elements.push(renderTable(tableHeader, tableRows));
  }

  return <div className="markdown-content">{elements}</div>;
}

/** 内联 Markdown：处理 **粗体** *斜体* */
function renderInlineMarkdown(text: string): ReactNode {
  const parts = text.split(/(\*\*.*?\*\*|\*.*?\*)/g);
  return parts.map((part, i) => {
    if (part.startsWith("**") && part.endsWith("**")) {
      return <strong key={i} className="font-bold text-text-primary">{part.slice(2, -2)}</strong>;
    }
    if (part.startsWith("*") && part.endsWith("*")) {
      return <em key={i} className="italic">{part.slice(1, -1)}</em>;
    }
    return part;
  });
}

/** 简易 Markdown 表格 */
function renderTable(header: string[], rows: string[][]): ReactNode {
  return (
    <table className="w-full my-2 text-small border-collapse">
      <thead>
        <tr>
          {header.map((h, i) => (
            <th key={i} className="border border-divider px-2 py-1 bg-surface-input text-text-secondary font-medium text-left">
              {renderInlineMarkdown(h)}
            </th>
          ))}
        </tr>
      </thead>
      <tbody>
        {rows.map((row, ri) => (
          <tr key={ri}>
            {row.map((cell, ci) => (
              <td key={ci} className="border border-divider px-2 py-1 text-text-secondary">
                {renderInlineMarkdown(cell)}
              </td>
            ))}
          </tr>
        ))}
      </tbody>
    </table>
  );
}

type BubbleRole = "user" | "assistant";

interface BubbleProps {
  role: BubbleRole;
  children: ReactNode;
  className?: string;
  showCopy?: boolean;
  onCopy?: () => void;
  copied?: boolean;
}

/** 头像圆圈 */
function Avatar({ role }: { role: BubbleRole }) {
  const isUser = role === "user";
  return (
    <div
      className={`
        w-[34px] h-[34px] rounded-full flex items-center justify-center flex-shrink-0
        text-xs font-bold select-none
        ${isUser
          ? "bg-text-primary text-white"
          : "bg-sand-dark text-text-primary"
        }
      `}
    >
      {isUser ? "我" : "AI"}
    </div>
  );
}

export function Bubble({ role, children, className = "", showCopy, onCopy, copied }: BubbleProps) {
  const isUser = role === "user";

  return (
    <div
      className={`
        flex items-start gap-2.5 mb-4 bubble-enter
        ${isUser ? "flex-row-reverse" : "flex-row"}
        max-w-[88%] ${isUser ? "ml-auto" : "mr-auto"}
      `}
    >
      <Avatar role={role} />
      <div className="relative group">
        <div
          className={`
            px-3.5 py-2.5 text-body leading-relaxed
            ${isUser
              ? "bg-text-primary text-white rounded-bubble rounded-br-sm"
              : "bg-surface-card text-text-primary rounded-bubble rounded-bl-sm border border-warm-border"
            }
            ${className}
          `}
        >
          {role === "assistant" ? renderMarkdown(children as string) : children}
        </div>
        {/* 一键复制按钮 — AI 消息时显示 */}
        {showCopy && onCopy && (
          <button
            onClick={onCopy}
            className={`
              absolute -bottom-1 right-0 translate-y-full
              px-2 py-0.5 text-[0.65rem] font-medium
              rounded-tag border transition-all duration-200
              ${copied
                ? "bg-accent-green text-white border-accent-green"
                : "bg-white text-ink-tertiary border-warm-border hover:border-ink-tertiary hover:text-ink-secondary"
              }
              opacity-0 group-hover:opacity-100
              cursor-pointer whitespace-nowrap
            `}
          >
            {copied ? "✅ 已复制" : "📋 复制"}
          </button>
        )}
      </div>
    </div>
  );
}

/** 思考中骨架气泡 */
export function ThinkingBubble() {
  return (
    <div className="flex items-start gap-2.5 mb-4">
      <Avatar role="assistant" />
      <div className="bg-surface-card border border-warm-border rounded-bubble rounded-bl-sm px-4 py-3">
        <div className="flex gap-1.5">
          {[0, 1, 2].map((i) => (
            <span
              key={i}
              className="w-1.5 h-1.5 rounded-full bg-ink-tertiary"
              style={{
                animation: "dotBounce 1.3s ease-in-out infinite",
                animationDelay: `${i * 0.16}s`,
              }}
            />
          ))}
        </div>
      </div>
    </div>
  );
}
