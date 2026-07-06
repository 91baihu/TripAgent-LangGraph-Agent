/** 首页 — 响应式分屏布局：桌面左聊天右可视化，移动端 Tab 切换 */

import { useState, useRef, useEffect } from "react";
import { Bubble, ThinkingBubble } from "../../components/Bubble/Bubble";
import { Tag } from "../../components/Tag/Tag";
import { useChatStore } from "../../stores/chatStore";
import { useChatStream } from "../../hooks/useChatStream";
import { ToolStepChip, StepsSummary } from "./ToolStepCard";
import { VisualizationPanel } from "./VisualizationPanel";
import { ViewSwitcher, type MobileView } from "../../components/ViewSwitcher/ViewSwitcher";
import { SearchProgress } from "./SearchProgress";

const QUICK_SUGGESTIONS = [
  { emoji: "🏖️", label: "北京3日亲子游" },
  { emoji: "⛰️", label: "杭州周末游" },
  { emoji: "🎌", label: "大阪文化之旅" },
];

export function ChatPage() {
  const {
    messages,
    isStreaming,
    streamingReply,
    toolSteps,
    stepsCollapsed,
  } = useChatStore();
  const { sendMessage, cancelStream } = useChatStream();
  const [input, setInput] = useState("");
  const [mobileView, setMobileView] = useState<MobileView>("chat");
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // 自动滚到底部
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, streamingReply, toolSteps]);

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

  // ========== 空状态（无消息 + 未流式） ==========
  const showEmpty =
    messages.length === 0 && !isStreaming && !streamingReply;

  // ========== 聊天内容区 ==========
  const chatContent = (
    <div className="flex-1 overflow-y-auto px-4 py-4">
      {showEmpty ? (
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
          <h2 className="text-h2 text-text-primary mb-2">想去哪里旅行？</h2>
          <p className="text-body text-text-secondary mb-6 max-w-[260px]">
            告诉我你的需求，AI 为你量身规划行程
          </p>
          <div className="flex flex-wrap gap-2 justify-center">
            {QUICK_SUGGESTIONS.map((s) => (
              <Tag
                key={s.label}
                variant="default"
                onClick={() => {
                  if (!isStreaming) {
                    setMobileView("chat");
                    sendMessage(s.label);
                  }
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

          {/* 流式回复（增量显示） */}
          {streamingReply && (
            <Bubble role="assistant">{streamingReply}</Bubble>
          )}

          {/* 思考中（LLM 还没开始输出文本） */}
          {isStreaming && !streamingReply && toolSteps.length === 0 && (
            <ThinkingBubble />
          )}

          {/* 紧凑工具调用指示器（可折叠） */}
          {toolSteps.length > 0 && (
            <div className="my-2 py-1">
              {stepsCollapsed ? (
                <StepsSummary
                  count={toolSteps.length}
                  doneCount={toolSteps.filter((s) => s.result).length}
                  onExpand={() => useChatStore.getState().expandSteps()}
                />
              ) : (
                toolSteps.map((step) => (
                  <ToolStepChip key={step.step} step={step} />
                ))
              )}
            </div>
          )}
        </div>
      )}
      <div ref={messagesEndRef} />
    </div>
  );

  // ========== 输入栏 ==========
  const inputBar = (
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
          <button
            onClick={cancelStream}
            className="
              h-[44px] px-4 rounded-button bg-semantic-error text-white
              text-caption font-medium hover:opacity-90 active:scale-95
              transition-all flex-shrink-0
            "
          >
            停止
          </button>
        ) : (
          <button
            onClick={handleSend}
            disabled={!input.trim()}
            className="
              w-[44px] h-[44px] rounded-button
              bg-primary text-white shadow-button
              hover:bg-primary-hover active:scale-95
              disabled:opacity-40 disabled:active:scale-100
              flex items-center justify-center transition-all flex-shrink-0
            "
          >
            ✈️
          </button>
        )}
      </div>
    </div>
  );

  // ========== 移动端非聊天视图 ==========
  const mobilePanel = (view: MobileView) => {
    if (view === "chat") return null;
    return (
      <div className="flex-1 flex flex-col min-h-0">
        <VisualizationPanel
          variant="mobile"
          initialTab={view === "map" ? "map" : view === "rankings" ? "rankings" : "trace"}
          onBack={() => setMobileView("chat")}
        />
      </div>
    );
  };

  return (
    <div className="flex flex-col h-dvh">
      {/* Header */}
      <header
        className="
          flex-shrink-0 h-14 bg-surface-card border-b border-divider
          flex items-center justify-between px-4
        "
      >
        <h1 className="text-h3 text-primary font-bold">✈️ TripAgent</h1>
        <div className="w-8 h-8 rounded-full bg-primary-light flex items-center justify-center text-primary text-small font-bold">
          T
        </div>
      </header>

      {/* ===== 桌面端：左右分屏 ===== */}
      <div className="hidden md:flex flex-1 min-h-0">
        {/* 左栏：聊天 — 居中限宽 */}
        <div className="flex-1 flex flex-col min-w-0 border-r border-divider">
          <div className="max-w-2xl mx-auto w-full flex flex-col flex-1 min-h-0">
            {chatContent}
            <SearchProgress />
            {inputBar}
          </div>
        </div>

        {/* 右栏：可视化面板 */}
        <div className="w-[420px] flex-shrink-0 flex flex-col min-h-0 bg-surface-page">
          <VisualizationPanel variant="desktop" />
        </div>
      </div>

      {/* ===== 移动端：Tab 切换 ===== */}
      <div className="flex md:hidden flex-1 flex-col min-h-0">
        {mobileView === "chat" ? (
          chatContent
        ) : (
          mobilePanel(mobileView)
        )}

        {/* 进度条（对话视图时显示） */}
        {mobileView === "chat" && <SearchProgress />}

        {/* 输入栏（对话视图时显示） */}
        {mobileView === "chat" && inputBar}

        {/* 视图切换器 */}
        <ViewSwitcher
          active={mobileView}
          onChange={(v) => setMobileView(v)}
        />
      </div>
    </div>
  );
}
