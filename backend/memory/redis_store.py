"""
Redis 短期记忆存储
存储当前会话上下文 + ReAct 推理中间态，TTL = 24h

注意：需要本地 Redis 运行在 localhost:6379
如无 Redis 环境，使用内存 dict fallback（开发模式）
"""
from __future__ import annotations

import json
from datetime import timedelta
from typing import Any

try:
    import redis
    _HAS_REDIS = True
except ImportError:
    _HAS_REDIS = False


class RedisStore:
    """Redis 短期记忆管理"""

    TTL_HOURS = 24  # 会话记忆 24 小时自动过期

    def __init__(self, redis_url: str = "redis://localhost:6379/0"):
        self._fallback: dict[str, Any] = {}
        self._client = None
        if _HAS_REDIS:
            try:
                self._client = redis.from_url(redis_url, decode_responses=True)
                self._client.ping()
                print("[Redis] ✅ 连接成功")
            except Exception as e:
                print(f"[Redis] ⚠️  连接失败（{e}），使用内存 fallback")
                self._client = None
        else:
            print("[Redis] ⚠️  未安装 redis 包，使用内存 fallback")

    @property
    def connected(self) -> bool:
        return self._client is not None

    # ── 会话上下文 ─────────────────────────────────────
    def save_session_context(self, session_id: str, context: dict) -> None:
        """保存当前会话上下文（对话历史 + ReAct 中间态）"""
        key = f"session:{session_id}:context"
        data = json.dumps(context, ensure_ascii=False)
        if self._client:
            self._client.setex(key, timedelta(hours=self.TTL_HOURS), data)
        else:
            self._fallback[key] = data

    def get_session_context(self, session_id: str) -> dict | None:
        """获取当前会话上下文"""
        key = f"session:{session_id}:context"
        if self._client:
            raw = self._client.get(key)
        else:
            raw = self._fallback.get(key)
        if raw:
            return json.loads(raw)
        return None

    def clear_session(self, session_id: str) -> None:
        """清除会话上下文"""
        key = f"session:{session_id}:context"
        if self._client:
            self._client.delete(key)
        else:
            self._fallback.pop(key, None)

    # ── ReAct 推理历史 ────────────────────────────────
    def append_react_step(self, session_id: str, step: dict) -> None:
        """追加一步 ReAct 推理记录（Thought/Action/Observation）"""
        key = f"session:{session_id}:react_history"
        data = json.dumps(step, ensure_ascii=False)
        if self._client:
            self._client.rpush(key, data)
            self._client.expire(key, timedelta(hours=self.TTL_HOURS))
        else:
            if key not in self._fallback:
                self._fallback[key] = []
            self._fallback[key].append(data)

    def get_react_history(self, session_id: str) -> list[dict]:
        """获取 ReAct 推理历史"""
        key = f"session:{session_id}:react_history"
        if self._client:
            raw_list = self._client.lrange(key, 0, -1)
        else:
            raw_list = self._fallback.get(key, [])
        return [json.loads(r) for r in raw_list]

    # ── 通用 KV ───────────────────────────────────────
    def set(self, key: str, value: str, ttl_hours: int = 24) -> None:
        if self._client:
            self._client.setex(key, timedelta(hours=ttl_hours), value)
        else:
            self._fallback[key] = value

    def get(self, key: str) -> str | None:
        if self._client:
            return self._client.get(key)
        return self._fallback.get(key)


# 全局单例
redis_store = RedisStore()
