"""
语义记忆管理（ChromaDB）
封装 retriever 的用户画像读写 + 周度 LLM 压缩摘要
"""
from __future__ import annotations

from rag.retriever import recall_user_memory, add_user_semantic_memory


def get_semantic_memories(user_id: str, query: str, top_k: int = 3) -> str:
    """从 ChromaDB 检索用户长期语义画像"""
    return recall_user_memory(user_id, query, top_k)


def save_semantic_memory(user_id: str, memory_text: str) -> None:
    """保存一条语义记忆到 ChromaDB"""
    add_user_semantic_memory(user_id, memory_text)
