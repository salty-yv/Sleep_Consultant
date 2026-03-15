"""
记忆管理器（三层记忆的统一入口）
"""
from __future__ import annotations

from memory.redis_store import redis_store
from memory.semantic import get_semantic_memories, save_semantic_memory
from memory.episodic import get_episodic_trend


class MemoryManager:
    """统一管理三层记忆的读写"""

    def __init__(self):
        self.redis = redis_store

    # ── 短期记忆（Redis）───────────────────────────
    def get_short_term(self, session_id: str) -> dict | None:
        return self.redis.get_session_context(session_id)

    def save_short_term(self, session_id: str, context: dict) -> None:
        self.redis.save_session_context(session_id, context)

    def append_react_step(self, session_id: str, step: dict) -> None:
        self.redis.append_react_step(session_id, step)

    def get_react_history(self, session_id: str) -> list[dict]:
        return self.redis.get_react_history(session_id)

    # ── 中期记忆（PostgreSQL）─────────────────────
    async def get_weekly_trend(self, db, user_id: str) -> list[dict]:
        return await get_episodic_trend(db, user_id)

    # ── 长期记忆（ChromaDB）──────────────────────
    def recall_long_term(self, user_id: str, query: str) -> str:
        return get_semantic_memories(user_id, query)

    def save_long_term(self, user_id: str, memory: str) -> None:
        save_semantic_memory(user_id, memory)


# 全局单例
memory_manager = MemoryManager()
