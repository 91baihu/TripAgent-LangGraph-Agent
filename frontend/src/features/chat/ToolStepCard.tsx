/** 工具步骤卡片 — 紧凑模式(聊天气泡内) + 完整模式(推理面板) */

import { useState } from "react";

interface ToolStep {
  step: number;
  tool: string;
  args: Record<string, unknown>;
  result?: string;
}

const TOOL_ICONS: Record<string, string> = {
  plan_route: "🗺️",
  search_restaurants: "🍜",
  search_hotels: "🏨",
  get_weather: "🌤️",
  search_attractions: "🏛️",
};

const TOOL_LABELS: Record<string, string> = {
  plan_route: "路线规划",
  search_restaurants: "搜索餐厅",
  search_hotels: "搜索酒店",
  get_weather: "查询天气",
  search_attractions: "搜索景点",
};

interface ToolStepCardProps {
  step: ToolStep;
  compact?: boolean;
}

/** 紧凑模式：消息流中的一行小标签 */
export function ToolStepChip({ step }: { step: ToolStep }) {
  const icon = TOOL_ICONS[step.tool] || "🔧";
  const label = TOOL_LABELS[step.tool] || step.tool;
  const done = !!step.result;

  return (
    <div className="flex items-center gap-2 px-3 py-1.5 my-1 text-caption text-text-secondary">
      <span>{icon}</span>
      <span className="text-text-primary font-medium">{label}</span>
      {done ? (
        <span className="text-semantic-success text-small">✓ 完成</span>
      ) : (
        <span className="text-primary text-small animate-pulse">执行中...</span>
      )}
    </div>
  );
}

/** 完整模式：推理面板中的可展开卡片 */
export function ToolStepCard({ step, compact = false }: ToolStepCardProps) {
  const [showArgs, setShowArgs] = useState(false);
  const [showResult, setShowResult] = useState(false);
  const icon = TOOL_ICONS[step.tool] || "🔧";
  const label = TOOL_LABELS[step.tool] || step.tool;

  if (compact) {
    return <ToolStepChip step={step} />;
  }

  return (
    <div className="bg-surface-card border border-warm-border rounded-card p-3 card-enter hover:border-ink transition-colors duration-200">
      {/* 头部：步骤号 + 图标 + 工具名 */}
      <div className="flex items-center gap-2 mb-2">
        <span
          className={`w-6 h-6 rounded-full text-white text-small flex items-center justify-center font-bold ${
            step.result ? "bg-teal" : "bg-ink"
          }`}
        >
          {step.step}
        </span>
        <span className="text-lg">{icon}</span>
        <span className="text-body text-text-primary font-medium">{label}</span>
        {step.result ? (
          <span className="text-caption text-semantic-success ml-auto">✓ 完成</span>
        ) : (
          <span className="text-caption text-primary ml-auto animate-pulse">
            ⏳ 执行中
          </span>
        )}
      </div>

      {/* 输入参数（可折叠） */}
      <div>
        <button
          onClick={() => setShowArgs(!showArgs)}
          className="text-small text-primary hover:text-primary-hover transition-colors"
        >
          {showArgs ? "▾" : "▸"} 输入参数
        </button>
        {showArgs && (
          <pre className="mt-1 p-2 bg-surface-input rounded-tag text-small text-text-secondary overflow-x-auto max-h-[120px] overflow-y-auto">
            {JSON.stringify(step.args, null, 2)}
          </pre>
        )}
      </div>

      {/* 返回结果（可折叠） */}
      {step.result && (
        <div className="mt-2">
          <button
            onClick={() => setShowResult(!showResult)}
            className="text-small text-primary hover:text-primary-hover transition-colors"
          >
            {showResult ? "▾" : "▸"} 返回结果
          </button>
          {showResult && (
            <pre className="mt-1 p-2 bg-surface-input rounded-tag text-small text-text-secondary overflow-x-auto max-h-[200px] overflow-y-auto whitespace-pre-wrap">
              {step.result}
            </pre>
          )}
        </div>
      )}
    </div>
  );
}

/** 折叠摘要：流式完成后显示一行 "已完成 N 步检索" */
export function StepsSummary({
  count,
  doneCount,
  onExpand,
}: {
  count: number;
  doneCount: number;
  onExpand: () => void;
}) {
  return (
    <button
      onClick={onExpand}
      className="flex items-center gap-2 px-3 py-2 my-1 w-full text-left
                 bg-surface-card border border-divider rounded-card
                 hover:bg-surface-input transition-colors"
    >
      <span className="text-semantic-success font-medium text-caption">
        ✅ 已完成 {doneCount}/{count} 步检索
      </span>
      <span className="text-text-tertiary text-small ml-auto">点击展开 ▸</span>
    </button>
  );
}
