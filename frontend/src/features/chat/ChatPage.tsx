/** 首页 — 响应式分屏布局：桌面左聊天右可视化，移动端 Tab 切换 */

import { useState, useRef, useEffect, useCallback } from "react";
import { Bubble, ThinkingBubble } from "../../components/Bubble/Bubble";
import { ChatSkeleton } from "../../components/Skeleton/Skeleton";
import { useChatStore } from "../../stores/chatStore";
import { useChatStream } from "../../hooks/useChatStream";
import { useDeviceFingerprint } from "../../hooks/useDeviceFingerprint";
import { ToolStepChip, StepsSummary } from "./ToolStepCard";
import { VisualizationPanel } from "./VisualizationPanel";
import { ViewSwitcher, type MobileView } from "../../components/ViewSwitcher/ViewSwitcher";
import { SearchProgress } from "./SearchProgress";
import { UserMenu } from "../../components/UserMenu/UserMenu";
import { QuotaBar } from "../../components/QuotaBar/QuotaBar";
import { showToast } from "../../components/Toast/ToastContainer";

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
  const [copiedId, setCopiedId] = useState<string | null>(null);

  // 设备指纹初始化（仅首次加载时异步生成）
  useDeviceFingerprint();

  // 一键复制单条消息
  const handleCopyMessage = useCallback(async (content: string, id: string) => {
    try {
      await navigator.clipboard.writeText(content);
      setCopiedId(id);
      showToast("✅ 已复制到剪贴板");
      setTimeout(() => setCopiedId(null), 2000);
    } catch {
      showToast("复制失败", "error");
    }
  }, []);

  // 一键复制全部对话
  const handleCopyAll = useCallback(async () => {
    const allContent = messages
      .map((m) => `${m.role === "user" ? "🧑 我" : "🤖 AI"}\n${m.content}`)
      .join("\n\n---\n\n");
    const finalContent = allContent + (streamingReply ? `\n\n---\n\n🤖 AI\n${streamingReply}` : "");
    try {
      await navigator.clipboard.writeText(finalContent);
      showToast("✅ 全部对话已复制");
    } catch {
      showToast("复制失败", "error");
    }
  }, [messages, streamingReply]);

  // 自动滚到底部 — 流式时即时滚动防抖动，普通消息平滑滚动
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const lastUserMsgRef = useRef(false);

  useEffect(() => {
    const el = messagesEndRef.current;
    if (!el) return;

    const lastMsg = messages[messages.length - 1];
    const isNewUserMsg = lastMsg?.role === "user" && !lastUserMsgRef.current;
    lastUserMsgRef.current = lastMsg?.role === "user";

    if (isStreaming) {
      // 流式中：即时滚动，避免 smooth 堆积导致抖动
      el.scrollIntoView({ behavior: "auto" });
    } else if (isNewUserMsg) {
      // 新用户消息：平滑滚动到输入区
      el.scrollIntoView({ behavior: "smooth" });
    } else {
      el.scrollIntoView({ behavior: "auto" });
    }
  }, [messages, streamingReply, toolSteps, isStreaming]);

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
          {messages.map((msg, idx) => {
            const isLastAiMsg =
              msg.role === "assistant" &&
              (idx === messages.length - 1 || !messages.slice(idx + 1).some(m => m.role === "assistant"));
            return (
              <Bubble
                key={msg.id}
                role={msg.role}
                showCopy={msg.role === "assistant"}
                copied={copiedId === msg.id}
                onCopy={
                  msg.role === "assistant"
                    ? () => handleCopyMessage(msg.content, msg.id)
                    : undefined
                }
              >
                {msg.content}
              </Bubble>
            );
          })}

          {/* 流式回复（增量显示） */}
          {streamingReply && (
            <Bubble role="assistant">{streamingReply}</Bubble>
          )}

          {/* 等待首响应骨架屏（刚发送消息还未收到任何回应时） */}
          {isStreaming && !streamingReply && toolSteps.length === 0 && messages.length > 0 && (
            <>
              <ThinkingBubble />
              <ChatSkeleton />
            </>
          )}

          {/* 思考中（纯初始状态：无历史消息 + 流式中 + 无工具调用） */}
          {isStreaming && !streamingReply && toolSteps.length === 0 && messages.length === 0 && (
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

          {/* 全局复制全部对话按钮（有消息且不流式中时显示） */}
          {messages.length > 0 && !isStreaming && (
            <div className="flex justify-center mt-3 mb-2">
              <button
                onClick={handleCopyAll}
                className="
                  inline-flex items-center gap-1.5 px-3 py-1.5
                  text-xs text-ink-tertiary hover:text-ink-secondary
                  bg-transparent hover:bg-sand-dark
                  rounded-button border border-warm-border hover:border-ink-tertiary
                  transition-all duration-200 cursor-pointer
                "
              >
                📋 复制全部对话
              </button>
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
        <UserMenu />
      </header>

      {/* 额度进度条 */}
      <QuotaBar />

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
