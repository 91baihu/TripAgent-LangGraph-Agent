"""Token 用量追踪与成本估算

提供：
- Token 计数（基于 tiktoken 或字符估算）
- 成本计算（DeepSeek 定价模型）
- 按请求/会话/用户维度的用量统计
- 预算告警

DeepSeek 定价（2024）：
- deepseek-chat: 输入 ¥1/1M tokens, 输出 ¥2/1M tokens
"""

import os
import time
import threading
from dataclasses import dataclass, field
from typing import Optional, Dict, List, Tuple
from collections import defaultdict


# ========== 定价配置 ==========
MODEL_PRICING = {
    "deepseek-chat": {
        "input_price_per_1m": 1.0,   # ¥1 / 1M tokens
        "output_price_per_1m": 2.0,  # ¥2 / 1M tokens
    },
    "deepseek-reasoner": {
        "input_price_per_1m": 4.0,
        "output_price_per_1m": 16.0,
    },
}


@dataclass
class TokenUsage:
    """单次调用的 token 用量"""
    model: str = "deepseek-chat"
    input_tokens: int = 0
    output_tokens: int = 0
    input_cost: float = 0.0
    output_cost: float = 0.0

    @property
    def total_tokens(self) -> int:
        return self.input_tokens + self.output_tokens

    @property
    def total_cost(self) -> float:
        return self.input_cost + self.output_cost


@dataclass
class SessionStats:
    """会话维度的统计"""
    session_id: str = ""
    user_id: str = ""
    call_count: int = 0
    total_input_tokens: int = 0
    total_output_tokens: int = 0
    total_cost: float = 0.0
    usages: List[TokenUsage] = field(default_factory=list)
    start_time: float = field(default_factory=time.time)

    def add_usage(self, usage: TokenUsage):
        self.call_count += 1
        self.total_input_tokens += usage.input_tokens
        self.total_output_tokens += usage.output_tokens
        self.total_cost += usage.total_cost
        self.usages.append(usage)

    @property
    def avg_tokens_per_call(self) -> float:
        if self.call_count == 0:
            return 0.0
        return (self.total_input_tokens + self.total_output_tokens) / self.call_count


class TokenTracker:
    """Token 用量追踪器

    Usage:
        tracker = TokenTracker()

        # 记录调用
        usage = tracker.record_call(
            model="deepseek-chat",
            input_text="你好",
            output_text="你好！有什么可以帮你的？",
        )

        # 查看统计
        stats = tracker.get_session_stats(session_id)
        print(f"本次会话花费: ¥{stats.total_cost:.4f}")
    """

    def __init__(self, alert_threshold_per_day: float = 50.0):
        self.alert_threshold = alert_threshold_per_day
        self._sessions: Dict[str, SessionStats] = {}      # session_id → stats
        self._user_daily: Dict[str, float] = defaultdict(float)  # user_id → daily cost
        self._total_cost: float = 0.0
        self._lock = threading.Lock()

        # Tokenizer 检测
        self._tokenizer = None
        self._tokenizer_name = "char_estimate"

    # ========== Token 计数 ==========

    def count_tokens(self, text: str, model: str = "deepseek-chat") -> int:
        """计算文本的 token 数量

        优先级：tiktoken > 字符估算
        """
        # 尝试 tiktoken
        if self._tokenizer is None:
            self._init_tokenizer(model)

        if self._tokenizer:
            try:
                return len(self._tokenizer.encode(text))
            except Exception:
                pass

        # 字符估算：中文 ~1.5 chars/token，英文 ~4 chars/token
        return self._estimate_tokens(text)

    def _init_tokenizer(self, model: str):
        """初始化 tokenizer"""
        try:
            import tiktoken
            # DeepSeek 兼容 OpenAI tokenizer
            try:
                self._tokenizer = tiktoken.encoding_for_model(model)
            except KeyError:
                self._tokenizer = tiktoken.get_encoding("cl100k_base")
            self._tokenizer_name = "tiktoken"
        except ImportError:
            self._tokenizer = None
            self._tokenizer_name = "char_estimate"

    @staticmethod
    def _estimate_tokens(text: str) -> int:
        """基于字符估算 token 数量

        中文：约 1 字符 ≈ 1.5 tokens
        英文：约 1 单词 ≈ 1.3 tokens
        """
        chinese_chars = sum(1 for c in text if '一' <= c <= '鿿')
        other_chars = len(text) - chinese_chars
        # 粗略：中文字符 / 1.5 + 其他字符 / 4
        import math
        return max(1, math.ceil(chinese_chars / 1.5 + other_chars / 4))

    # ========== 成本计算 ==========

    @staticmethod
    def calculate_cost(model: str, input_tokens: int, output_tokens: int) -> Tuple[float, float]:
        """计算输入和输出的成本

        Returns:
            (input_cost, output_cost) 单位：元
        """
        pricing = MODEL_PRICING.get(model, MODEL_PRICING["deepseek-chat"])
        input_cost = input_tokens / 1_000_000 * pricing["input_price_per_1m"]
        output_cost = output_tokens / 1_000_000 * pricing["output_price_per_1m"]
        return (input_cost, output_cost)

    # ========== 用量记录 ==========

    def record_call(
        self,
        model: str = "deepseek-chat",
        input_messages: list = None,
        output_text: str = "",
        input_tokens: int = 0,
        output_tokens: int = 0,
        session_id: str = "",
        user_id: str = "anonymous",
    ) -> TokenUsage:
        """记录一次 LLM 调用

        Args:
            model: 模型名称
            input_messages: 输入消息列表（自动计算 token）
            output_text: 输出文本
            input_tokens: 手动指定输入 token 数（为0时自动计算）
            output_tokens: 手动指定输出 token 数（为0时自动计算）
            session_id: 会话 ID
            user_id: 用户 ID
        """
        # 自动计算 token
        if input_tokens == 0 and input_messages:
            input_text = ""
            for msg in input_messages:
                content = msg.get("content", "") if isinstance(msg, dict) else str(msg)
                input_text += content
            input_tokens = self.count_tokens(input_text, model)

        if output_tokens == 0 and output_text:
            output_tokens = self.count_tokens(output_text, model)

        # 计算成本
        input_cost, output_cost = self.calculate_cost(model, input_tokens, output_tokens)

        usage = TokenUsage(
            model=model,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            input_cost=input_cost,
            output_cost=output_cost,
        )

        # 记录到会话
        with self._lock:
            if session_id:
                if session_id not in self._sessions:
                    self._sessions[session_id] = SessionStats(
                        session_id=session_id,
                        user_id=user_id,
                    )
                self._sessions[session_id].add_usage(usage)

            if user_id:
                self._user_daily[user_id] += usage.total_cost

            self._total_cost += usage.total_cost

        return usage

    # ========== 查询统计 ==========

    def get_session_stats(self, session_id: str) -> Optional[SessionStats]:
        """获取会话统计"""
        return self._sessions.get(session_id)

    def get_user_daily_cost(self, user_id: str) -> float:
        """获取用户当日花费"""
        return self._user_daily.get(user_id, 0.0)

    def get_total_cost(self) -> float:
        """获取总花费"""
        return self._total_cost

    def is_over_budget(self, user_id: str = "") -> bool:
        """检查是否超出预算"""
        if user_id:
            return self._user_daily.get(user_id, 0.0) >= self.alert_threshold
        return self._total_cost >= self.alert_threshold

    def get_summary(self, session_id: str = "") -> Dict:
        """获取用量摘要"""
        if session_id:
            stats = self._sessions.get(session_id)
            if not stats:
                return {}
            return {
                "session_id": stats.session_id,
                "call_count": stats.call_count,
                "input_tokens": stats.total_input_tokens,
                "output_tokens": stats.total_output_tokens,
                "total_tokens": stats.total_input_tokens + stats.total_output_tokens,
                "total_cost_yuan": round(stats.total_cost, 6),
                "avg_tokens_per_call": round(stats.avg_tokens_per_call, 1),
                "duration_seconds": round(time.time() - stats.start_time, 1),
            }

        return {
            "total_sessions": len(self._sessions),
            "total_cost_yuan": round(self._total_cost, 6),
            "alert_threshold_yuan": self.alert_threshold,
            "tokenizer": self._tokenizer_name,
        }

    def format_cost_report(self, session_id: str = "") -> str:
        """生成人类可读的成本报告"""
        summary = self.get_summary(session_id)
        if not summary:
            return "📊 暂无用量数据"

        lines = ["## 📊 Token 用量报告", ""]
        if session_id:
            lines.append(f"| 指标 | 数值 |")
            lines.append(f"|------|------|")
            lines.append(f"| 会话 ID | {summary.get('session_id', '-')} |")
            lines.append(f"| 调用次数 | {summary.get('call_count', 0)} |")
            lines.append(f"| 输入 Tokens | {summary.get('input_tokens', 0):,} |")
            lines.append(f"| 输出 Tokens | {summary.get('output_tokens', 0):,} |")
            lines.append(f"| 总 Tokens | {summary.get('total_tokens', 0):,} |")
            lines.append(f"| 预估费用 | ¥{summary.get('total_cost_yuan', 0):.4f} |")
            lines.append(f"| 平均 Tokens/调用 | {summary.get('avg_tokens_per_call', 0)} |")
            lines.append(f"| 会话时长 | {summary.get('duration_seconds', 0)}s |")
        else:
            lines.append(f"| 指标 | 数值 |")
            lines.append(f"|------|------|")
            lines.append(f"| 总会话数 | {summary.get('total_sessions', 0)} |")
            lines.append(f"| 累计费用 | ¥{summary.get('total_cost_yuan', 0):.4f} |")
            lines.append(f"| 告警阈值 | ¥{summary.get('alert_threshold_yuan', 0)}/天 |")
            lines.append(f"| Tokenizer | {summary.get('tokenizer', 'unknown')} |")

        return "\n".join(lines)


# 全局单例
token_tracker = TokenTracker(alert_threshold_per_day=50.0)
