"""TripAgent FastAPI 中间件集合

提供：
- 请求 ID 注入与传递
- 请求耗时统计
- LLM API 调用熔断器
- 限流中间件
"""

import time
import uuid
import asyncio
from typing import Optional
from collections import defaultdict

from fastapi import Request, HTTPException


# ========== 请求 ID 中间件 ==========
class RequestIDMiddleware:
    """注入 X-Request-ID，若请求未携带则自动生成"""

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        # 从 headers 中获取或生成
        headers = dict(scope.get("headers", []))
        request_id = headers.get(b"x-request-id")
        if request_id:
            request_id = request_id.decode()
        else:
            request_id = str(uuid.uuid4())[:8]

        scope["request_id"] = request_id

        async def send_wrapper(message):
            if message["type"] == "http.response.start":
                headers_list = list(message.get("headers", []))
                headers_list.append(
                    (b"x-request-id", request_id.encode())
                )
                message["headers"] = headers_list
            await send(message)

        await self.app(scope, receive, send_wrapper)


# ========== 访问日志中间件 ==========
class AccessLogMiddleware:
    """记录每个 HTTP 请求的 method、path、status、耗时"""

    def __init__(self, app, logger=None):
        self.app = app
        if logger is None:
            from .logging import get_logger

            logger = get_logger("access")
        self.logger = logger

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        start = time.time()
        path = scope.get("path", "")
        method = scope.get("method", "")

        async def send_wrapper(message):
            if message["type"] == "http.response.start":
                latency_ms = (time.time() - start) * 1000
                status = message.get("status", 0)
                self.logger.info(
                    f"{method} {path}",
                    method=method,
                    path=path,
                    status=status,
                    latency_ms=round(latency_ms, 1),
                )
            await send(message)

        await self.app(scope, receive, send_wrapper)


# ========== LLM 熔断器 ==========
class CircuitBreaker:
    """LLM API 调用熔断器

    状态机: CLOSED → (连续失败5次) → OPEN → (等待30s) → HALF_OPEN → (成功) → CLOSED
    """

    def __init__(self, failure_threshold: int = 5, recovery_timeout: float = 30.0):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self._failure_count = 0
        self._last_failure_time = 0.0
        self._state = "CLOSED"  # CLOSED | OPEN | HALF_OPEN

    @property
    def state(self) -> str:
        return self._state

    def call(self, coro):
        """包装异步调用，自动熔断

        Usage:
            result = await circuit_breaker.call(llm.ainvoke(messages))
        """
        if self._state == "OPEN":
            if time.time() - self._last_failure_time > self.recovery_timeout:
                self._state = "HALF_OPEN"
            else:
                raise CircuitBreakerOpenError(
                    f"LLM 服务熔断中，{self.recovery_timeout - (time.time() - self._last_failure_time):.0f}s 后重试"
                )

        try:
            result = coro()
            self._on_success()
            return result
        except Exception:
            self._on_failure()
            raise

    def _on_success(self):
        self._failure_count = 0
        self._state = "CLOSED"

    def _on_failure(self):
        self._failure_count += 1
        self._last_failure_time = time.time()
        if self._failure_count >= self.failure_threshold:
            self._state = "OPEN"


class CircuitBreakerOpenError(Exception):
    """熔断器开启时抛出的异常"""
    pass


# 全局 LLM 熔断器
llm_circuit_breaker = CircuitBreaker(failure_threshold=5, recovery_timeout=30.0)


# ========== Token Bucket 限流器 ==========
class TokenBucketRateLimiter:
    """令牌桶限流器 — 支持按 key 限流

    免费用户: 3次/天
    Pro 用户: 100次/天
    IP 级别: 30次/分钟
    """

    def __init__(self):
        self._buckets: dict = {}
        self._lock = asyncio.Lock()

    async def is_allowed(
        self,
        key: str,
        max_tokens: int,
        refill_seconds: float = 60.0,
    ) -> bool:
        """检查是否允许通过

        Args:
            key: 限流 key (user_id / ip)
            max_tokens: 时间窗口内最大请求数
            refill_seconds: Token 补充周期（秒）

        Returns:
            True = 允许, False = 超出限制
        """
        async with self._lock:
            now = time.time()
            bucket = self._buckets.get(key)

            if bucket is None or (now - bucket["last_refill"]) > refill_seconds:
                # 新时间窗口，重置
                self._buckets[key] = {
                    "tokens": max_tokens - 1,
                    "last_refill": now,
                }
                return True

            if bucket["tokens"] > 0:
                bucket["tokens"] -= 1
                return True

            return False

    def get_remaining(self, key: str) -> int:
        """查看剩余可用次数"""
        bucket = self._buckets.get(key)
        return bucket["tokens"] if bucket else 0


# 全局限流器
rate_limiter = TokenBucketRateLimiter()
