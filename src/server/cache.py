"""Redis 缓存层

提供：
- 工具调用结果缓存（去重）
- 会话状态缓存
- 限流计数器
"""

import os
import json
import hashlib
from typing import Optional, Any
from datetime import timedelta

# ========== Redis 客户端（可选依赖） ==========
try:
    import redis.asyncio as aioredis

    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False


def get_redis_url() -> str:
    """从环境变量构建 Redis URL"""
    return os.getenv("REDIS_URL", "redis://localhost:6379/0")


class CacheService:
    """Redis 缓存服务

    Fallback: 如果 Redis 不可用，降级为内存 dict（仅开发环境）
    """

    def __init__(self, redis_url: str = None):
        self._redis_url = redis_url or get_redis_url()
        self._redis = None
        self._fallback: dict = {}  # 内存降级

    async def _get_redis(self):
        """延迟连接 Redis"""
        if self._redis is None and REDIS_AVAILABLE:
            try:
                self._redis = aioredis.from_url(
                    self._redis_url,
                    encoding="utf-8",
                    decode_responses=True,
                )
                await self._redis.ping()
            except Exception:
                self._redis = None  # 连接失败，使用降级
        return self._redis

    # ===== 工具调用缓存 =====
    @staticmethod
    def _tool_cache_key(tool_name: str, args: dict) -> str:
        """生成工具调用缓存键"""
        arg_str = json.dumps(args, sort_keys=True, ensure_ascii=False)
        arg_hash = hashlib.md5(arg_str.encode()).hexdigest()[:12]
        return f"tool:{tool_name}:{arg_hash}"

    async def get_tool_result(self, tool_name: str, args: dict) -> Optional[str]:
        """查询缓存的工具调用结果"""
        key = self._tool_cache_key(tool_name, args)

        r = await self._get_redis()
        if r:
            result = await r.get(key)
            return result.decode() if isinstance(result, bytes) else result

        # 降级到内存
        entry = self._fallback.get(key)
        if entry:
            return entry["value"]
        return None

    async def set_tool_result(self, tool_name: str, args: dict, result: str, ttl: int = 300):
        """缓存工具调用结果（默认 5 分钟）"""
        key = self._tool_cache_key(tool_name, args)

        r = await self._get_redis()
        if r:
            await r.setex(key, ttl, result)
            return

        # 降级到内存
        import time
        self._fallback[key] = {
            "value": result,
            "expires_at": time.time() + ttl,
        }

    # ===== 会话缓存 =====
    async def get_session(self, session_id: str) -> Optional[dict]:
        """获取会话状态"""
        r = await self._get_redis()
        if r:
            data = await r.get(f"session:{session_id}")
            if data:
                return json.loads(data.decode() if isinstance(data, bytes) else data)
            return None

        entry = self._fallback.get(f"session:{session_id}")
        return entry["value"] if entry else None

    async def set_session(self, session_id: str, data: dict, ttl: int = 1800):
        """保存会话状态（默认 30 分钟）"""
        r = await self._get_redis()
        if r:
            await r.setex(f"session:{session_id}", ttl, json.dumps(data))
            return

        import time
        self._fallback[f"session:{session_id}"] = {
            "value": data,
            "expires_at": time.time() + ttl,
        }

    # ===== 限流计数器 =====
    async def increment_counter(self, key: str, window_seconds: int = 60) -> int:
        """自增计数器，返回当前值"""
        r = await self._get_redis()
        if r:
            count = await r.incr(f"rate:{key}")
            if count == 1:
                await r.expire(f"rate:{key}", window_seconds)
            return count

        # 降级到内存
        import time
        entry = self._fallback.get(f"rate:{key}")
        now = time.time()
        if entry and (now - entry["start"]) < window_seconds:
            entry["count"] += 1
        else:
            self._fallback[f"rate:{key}"] = {"count": 1, "start": now}
        return self._fallback[f"rate:{key}"]["count"]

    # ===== 同步工具调用缓存（供 LangGraph 同步工具使用） =====
    def get_tool_result_sync(self, tool_name: str, args: dict) -> Optional[str]:
        """同步查询缓存的工具调用结果（仅使用内存降级）"""
        key = self._tool_cache_key(tool_name, args)
        import time
        entry = self._fallback.get(key)
        if entry and time.time() < entry.get("expires_at", 0):
            return entry["value"]
        return None

    def set_tool_result_sync(self, tool_name: str, args: dict, result: str, ttl: int = 300):
        """同步缓存工具调用结果（仅使用内存降级）"""
        key = self._tool_cache_key(tool_name, args)
        import time
        self._fallback[key] = {
            "value": result,
            "expires_at": time.time() + ttl,
        }

    # ===== 通用键值缓存（验证码等） =====
    async def get(self, key: str) -> Optional[str]:
        """获取通用缓存值"""
        r = await self._get_redis()
        if r:
            result = await r.get(key)
            return result.decode() if isinstance(result, bytes) else result

        import time
        entry = self._fallback.get(key)
        if entry and time.time() < entry.get("expires_at", 0):
            return entry["value"]
        return None

    async def set(self, key: str, value: str, ttl: int = 300):
        """设置通用缓存值（默认 5 分钟）"""
        r = await self._get_redis()
        if r:
            await r.setex(key, ttl, value)
            return

        import time
        self._fallback[key] = {
            "value": value,
            "expires_at": time.time() + ttl,
        }

    async def delete(self, key: str):
        """删除通用缓存键"""
        r = await self._get_redis()
        if r:
            await r.delete(key)
            return

        self._fallback.pop(key, None)

    # ===== 健康检查 =====
    async def ping(self) -> bool:
        r = await self._get_redis()
        if r:
            try:
                return await r.ping()
            except Exception:
                return False
        return bool(self._fallback is not None)  # 降级模式始终"可用"


# 全局缓存单例
cache_service = CacheService()
