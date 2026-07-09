/** 推理追踪面板 — 展示 Agent 每一步工具调用的完整信息 */

import { useChatStore } from "../../stores/chatStore";
import { ToolStepCard } from "./ToolStepCard";

export function ReasoningTrace() {
  const { toolSteps } = useChatStore();

  if (toolSteps.length === 0) {
    return (
      <div className="flex-1 flex items-center justify-center py-12">
        <div className="text-center">
          <span className="text-4xl block mb-2">🔍</span>
          <p className="text-body text-text-secondary mb-1">
            推理过程将在此显示
          </p>
          <p className="text-caption text-text-tertiary">
            Agent 的每一步工具调用和思考过程透明可见
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="flex flex-col h-full">
      {/* 统计摘要 */}
      <div className="flex-shrink-0 px-4 py-3 border-b border-divider">
        <h3 className="text-h3 text-text-primary mb-2">🔍 推理过程追踪</h3>
        <div className="flex items-center gap-4 px-3 py-2.5 bg-sand rounded-xl">
          <div className="text-center flex-1">
            <div className="text-xl font-extrabold text-ink">{toolSteps.length}</div>
            <div className="text-[0.65rem] text-ink-tertiary">总步骤</div>
          </div>
          <div className="w-px h-8 bg-warm-border" />
          <div className="text-center flex-1">
            <div className="text-xl font-extrabold text-teal">
              {toolSteps.filter((s) => s.result).length}
            </div>
            <div className="text-[0.65rem] text-ink-tertiary">已完成</div>
          </div>
          <div className="w-px h-8 bg-warm-border" />
          <div className="text-center flex-1">
            <div className="text-xl font-extrabold text-ink">
              {toolSteps.length - toolSteps.filter((s) => s.result).length}
            </div>
            <div className="text-[0.65rem] text-ink-tertiary">进行中</div>
          </div>
        </div>
      </div>

      {/* 步骤列表 */}
      <div className="flex-1 overflow-y-auto p-4 space-y-3">
        {toolSteps.map((step) => (
          <ToolStepCard key={step.step} step={step} />
        ))}
      </div>
    </div>
  );
}
