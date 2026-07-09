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
        /* 空状态 — Demo V3 编辑风格 */
        <div className="flex flex-col items-center justify-center h-full text-center">
          <div
            className="
              w-[88px] h-[88px] rounded-[24px] flex items-center justify-center
              bg-sand-dark mb-5 animate-breathe
            "
          >
            <span className="text-[2.6rem]">✈️</span>
          </div>
          <h2 className="font-serif text-[1.8rem] font-black text-text-primary mb-1.5">
            想去哪里？
          </h2>
          <p className="text-body text-ink-secondary mb-6 max-w-[260px]">
            告诉我你的旅行需求，AI 为你规划旅程
          </p>
          <div className="flex flex-wrap gap-2 justify-center">
            {QUICK_SUGGESTIONS.map((s) => (
              <button
                key={s.label}
                onClick={() => {
                  if (!isStreaming) {
                    setMobileView("chat");
                    sendMessage(s.label);
                  }
                }}
                className="
                  inline-flex items-center px-4 py-2.5 rounded-full
                  text-sm font-medium bg-white border border-warm-border
                  text-text-primary transition-all duration-200
                  hover:border-text-primary hover:bg-sand hover:-translate-y-px
                  active:scale-95
                "
              >
                {s.emoji} {s.label}
              </button>
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
    <div className="flex-shrink-0 p-3 bg-white border-t border-warm-border2">
      <div className="flex items-end gap-2">
        <div className="flex-1 bg-sand rounded-[20px] border-[1.5px] border-warm-border focus-within:border-text-primary focus-within:bg-white transition-colors">
          <textarea
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="说出你的旅行需求..."
            rows={1}
            className="
              w-full bg-transparent text-body text-text-primary
              placeholder:text-ink-tertiary outline-none
              px-4 py-2.5 resize-none max-h-[120px]
            "
          />
        </div>
        {isStreaming ? (
          <button
            onClick={cancelStream}
            className="
              w-[42px] h-[42px] rounded-full bg-rust text-white
              text-lg font-bold hover:opacity-90 active:scale-95
              transition-all flex-shrink-0 flex items-center justify-center
            "
          >
            ■
          </button>
        ) : (
          <button
            onClick={handleSend}
            disabled={!input.trim()}
            className="
              w-[42px] h-[42px] rounded-full
              bg-text-primary text-white
              hover:bg-ink-secondary active:scale-95
              disabled:opacity-40 disabled:active:scale-100
              flex items-center justify-center transition-all flex-shrink-0
              text-lg
            "
          >
            →
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
          flex-shrink-0 h-[52px] bg-white/85 backdrop-blur border-b border-warm-border2
          flex items-center justify-between px-4 sticky top-0 z-30
        "
      >
        <h1 className="font-serif text-lg font-black text-text-primary">TripAgent</h1>
        <div className="w-[30px] h-[30px] rounded-full bg-text-primary flex items-center justify-center text-white text-[11px] font-bold">
          T
        </div>
      </header>

      {/* ===== 桌面端：左右分屏 ===== */}
      <div className="hidden md:flex flex-1 min-h-0">
        {/* 左栏：聊天 — 居中限宽 */}
        <div className="flex-1 flex flex-col min-w-0 border-r border-warm-border2">
          <div className="max-w-2xl mx-auto w-full flex flex-col flex-1 min-h-0">
            {chatContent}
            <SearchProgress />
            {inputBar}
          </div>
        </div>

        {/* 右栏：可视化面板 */}
        <div className="w-[420px] flex-shrink-0 flex flex-col min-h-0 bg-sand">
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
