/** 首页 — QQ 极简对话式旅行规划 */

import { useState, useRef, useEffect } from "react";
import { Bubble, ThinkingBubble } from "../../components/Bubble/Bubble";
import { Tag } from "../../components/Tag/Tag";
import { Button } from "../../components/Button/Button";
import { TripCardSkeleton } from "../../components/Skeleton/Skeleton";
import { useChatStore } from "../../stores/chatStore";
import { useChatStream } from "../../hooks/useChatStream";

const QUICK_SUGGESTIONS = [
  { emoji: "🏖️", label: "北京3日亲子游" },
  { emoji: "⛰️", label: "杭州周末游" },
  { emoji: "🎌", label: "大阪文化之旅" },
];

export function ChatPage() {
  const { messages, isStreaming, toolSteps } = useChatStore();
  const { sendMessage, cancelStream } = useChatStream();
  const [input, setInput] = useState("");
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // 自动滚到底部
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, toolSteps]);

  const handleSend = () => {
    const trimmed = input.trim();
    if (!trimmed || isStreaming) return;
    setInput("");
    sendMessage(trimmed);
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <div className="flex flex-col h-dvh">
      {/* 导航栏 */}
      <header
        className="
          flex-shrink-0 h-14 bg-surface-card border-b border-divider
          flex items-center justify-between px-4
        "
      >
        <h1 className="text-h3 text-primary font-bold">✈️ TripAgent</h1>
        {/* 预留头像位置 */}
        <div className="w-8 h-8 rounded-full bg-primary-light flex items-center justify-center text-primary text-small font-bold">
          T
        </div>
      </header>

      {/* 对话区 */}
      <div className="flex-1 overflow-y-auto px-4 py-4">
        {messages.length === 0 ? (
          /* 空状态 — QQ 风格 */
          <div className="flex flex-col items-center justify-center h-full text-center">
            <div
              className="
                w-20 h-20 rounded-full flex items-center justify-center
                bg-gradient-to-br from-primary to-primary-hover
                shadow-button mb-6
              "
            >
              <span className="text-4xl">✈️</span>
            </div>
            <h2 className="text-h2 text-text-primary mb-2">
              想去哪里旅行？
            </h2>
            <p className="text-body text-text-secondary mb-6 max-w-[260px]">
              告诉我你的需求，AI 为你量身规划行程
            </p>
            <div className="flex flex-wrap gap-2 justify-center">
              {QUICK_SUGGESTIONS.map((s) => (
                <Tag
                  key={s.label}
                  variant="default"
                  onClick={() => {
                    if (!isStreaming) sendMessage(s.label);
                  }}
                >
                  {s.emoji} {s.label}
                </Tag>
              ))}
            </div>
          </div>
        ) : (
          /* 消息列表 */
          <div className="space-y-1">
            {messages.map((msg) => (
              <Bubble key={msg.id} role={msg.role}>
                {msg.content}
              </Bubble>
            ))}

            {/* 思考中 */}
            {isStreaming && <ThinkingBubble />}

            {/* 工具调用展示 */}
            {toolSteps.length > 0 && (
              <div className="my-3 p-3 bg-primary-light rounded-card border border-primary/10">
                <p className="text-caption text-primary font-medium mb-2">
                  🔍 Agent 推理过程
                </p>
                {toolSteps.map((step) => (
                  <div key={step.step} className="text-small text-text-secondary mb-1">
                    <span className="text-text-primary font-medium">
                      Step {step.step}:
                    </span>{" "}
                    调用 <span className="text-primary">{step.tool}</span>
                    {step.result && (
                      <span className="text-semantic-success"> ✓ 完成</span>
                    )}
                  </div>
                ))}
              </div>
            )}
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* 输入栏 — QQ 风格底部固定 */}
      <div className="flex-shrink-0 p-3 bg-surface-card border-t border-divider">
        <div className="flex items-end gap-2">
          <div className="flex-1 bg-surface-input rounded-input border border-transparent focus-within:border-primary focus-within:bg-surface-card transition-colors">
            <textarea
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="说出你的旅行需求..."
              rows={1}
              className="
                w-full bg-transparent text-body text-text-primary
                placeholder:text-text-tertiary outline-none
                px-4 py-3 resize-none max-h-[120px]
              "
            />
          </div>
          {isStreaming ? (
            <Button variant="secondary" size="sm" onClick={cancelStream}>
              停止
            </Button>
          ) : (
            <button
              onClick={handleSend}
              disabled={!input.trim()}
              className="
                w-[44px] h-[44px] rounded-button
                bg-primary text-white shadow-button
                hover:bg-primary-hover active:scale-95
                disabled:opacity-40 disabled:active:scale-100
                flex items-center justify-center transition-all
              "
            >
              ✈️
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
