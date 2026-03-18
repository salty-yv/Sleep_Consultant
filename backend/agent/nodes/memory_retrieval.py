"""
节点2：memory_retrieval
同时拉取：
  - 近7日趋势（PostgreSQL，通过注入的 db 函数获取）
  - 长期语义画像（ChromaDB）
  - RAG 知识文档（ChromaDB）
"""
from __future__ import annotations

from agent.state import AgentState
from rag.retriever import recall_user_memory, search_sleep_knowledge


def memory_retrieval_node(
    state: AgentState,
    weekly_trend: list[dict] | None = None,
) -> dict:
    """
    从记忆层检索上下文：
      - weekly_trend 由 FastAPI 路由层预先查询 PostgreSQL 后注入
      - 语义记忆和 RAG 文档在此节点实时检索 ChromaDB
    """
    m = state.metrics or {}

    # 构造检索 Query（根据识别到的问题）
    issues_parts = []
    if m.get("rem_pct", 0) < 20:
        issues_parts.append("REM睡眠不足改善方法")
    if m.get("deep_pct", 0) < 15:
        issues_parts.append("深睡不足 N3 改善")
    if m.get("sleep_efficiency_pct", 0) < 85:
        issues_parts.append("睡眠效率低 改善")
    if m.get("awakening_count", 0) >= 4:
        issues_parts.append("夜间频繁觉醒 原因")

    query = " ".join(issues_parts) if issues_parts else "睡眠质量综合建议"

    # ── RAG 知识检索 ──────────────────────────────────────
    try:
        rag_docs = search_sleep_knowledge(query, top_k=3)
    except Exception as e:
        rag_docs = [f"[RAG检索失败：{e}]"]

    # ── 用户长期语义记忆 ──────────────────────────────────
    try:
        semantic_memories = recall_user_memory(state.user_id, query, top_k=3)
    except Exception as e:
        semantic_memories = f"[长期记忆检索失败：{e}]"

    return {
        "weekly_trend": weekly_trend or state.weekly_trend or [],
        "rag_docs": rag_docs,
        "semantic_memories": semantic_memories,
    }
