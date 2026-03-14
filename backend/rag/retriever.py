"""
Retriever - 从 ChromaDB 检索相关知识文档
供 LangGraph Agent 节点使用
"""
from __future__ import annotations

from pathlib import Path

from langchain_chroma import Chroma

from rag.embedder import get_embeddings
from rag.ingest import CHROMA_PERSIST_DIR, COLLECTION_RAG, COLLECTION_SEMANTIC

_rag_store: Chroma | None = None
_semantic_store: Chroma | None = None


def _get_rag_store() -> Chroma:
    global _rag_store
    if _rag_store is None:
        _rag_store = Chroma(
            collection_name=COLLECTION_RAG,
            embedding_function=get_embeddings(),
            persist_directory=CHROMA_PERSIST_DIR,
        )
    return _rag_store


def _get_semantic_store() -> Chroma:
    global _semantic_store
    if _semantic_store is None:
        _semantic_store = Chroma(
            collection_name=COLLECTION_SEMANTIC,
            embedding_function=get_embeddings(),
            persist_directory=CHROMA_PERSIST_DIR,
        )
    return _semantic_store


def search_sleep_knowledge(query: str, top_k: int = 3) -> list[str]:
    """
    从 RAG 知识库检索与查询最相关的内容片段。

    Args:
        query:  用户问题或睡眠问题描述，如 "REM不足改善方法"
        top_k:  返回文档数量

    Returns:
        相关文档内容字符串列表
    """
    store = _get_rag_store()
    docs = store.similarity_search(query, k=top_k)
    return [doc.page_content for doc in docs]


def recall_user_memory(user_id: str, query: str, top_k: int = 3) -> str:
    """
    从用户长期语义画像中检索相关历史规律。

    Args:
        user_id: 用户 ID
        query:   当前睡眠问题描述
        top_k:   返回条数

    Returns:
        拼接后的历史规律字符串
    """
    store = _get_semantic_store()
    docs = store.similarity_search(
        query,
        k=top_k,
        filter={"user_id": user_id},
    )
    if not docs:
        return "暂无该用户的长期历史记忆。"
    return "\n".join(f"- {doc.page_content}" for doc in docs)


def add_user_semantic_memory(user_id: str, memory_text: str) -> None:
    """
    将 LLM 总结的用户规律写入语义画像集合（Phase 2 周度压缩任务调用）。

    Args:
        user_id:     用户 ID
        memory_text: LLM 总结的语义记忆文本
    """
    from langchain_core.documents import Document

    store = _get_semantic_store()
    doc = Document(
        page_content=memory_text,
        metadata={"user_id": user_id, "type": "semantic"},
    )
    store.add_documents([doc])
