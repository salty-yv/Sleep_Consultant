"""
LangGraph Agent 状态定义
"""
from __future__ import annotations

from typing import Annotated, Any, Optional
from langgraph.graph.message import add_messages
from pydantic import BaseModel, Field


class AgentState(BaseModel):
    """LangGraph 全局状态，在各节点间传递"""

    # ── 输入 ──────────────────────────────────────────────
    user_id: str = ""
    date: str = ""
    record_id: Optional[int] = None

    # ── 睡眠数据 ──────────────────────────────────────────
    metrics: Optional[dict] = None       # SleepMetrics 序列化结果
    epochs_summary: Optional[str] = None # 供 LLM 阅读的 epoch 摘要文本

    # ── 记忆上下文 ────────────────────────────────────────
    weekly_trend: Optional[list[dict]] = None  # 近7日趋势（PostgreSQL）
    semantic_memories: Optional[str] = None    # 长期语义画像（ChromaDB）
    rag_docs: Optional[list[str]] = None       # RAG 检索到的医学知识

    # ── Agent 推理 ────────────────────────────────────────
    messages: Annotated[list, add_messages] = Field(default_factory=list)
    react_steps: list[dict] = Field(default_factory=list)  # Thought/Action/Obs 记录

    # ── 输出 ──────────────────────────────────────────────
    final_report: Optional[str] = None
    sleep_score: Optional[int] = None
    recommended_actions: list[dict] = Field(default_factory=list)  # IoT 建议动作

    class Config:
        arbitrary_types_allowed = True
