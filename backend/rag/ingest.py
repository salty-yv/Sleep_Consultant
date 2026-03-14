"""
Ingest - 知识文档向量化入库模块
将 knowledge_base/ 目录下的文档切片后存入 ChromaDB
"""
from __future__ import annotations

import os
from pathlib import Path

# 新的写法（兼容 LangChain 0.3+）
from langchain_text_splitters import MarkdownHeaderTextSplitter, RecursiveCharacterTextSplitter
#from langchain.text_splitter import MarkdownHeaderTextSplitter, RecursiveCharacterTextSplitter
from langchain_chroma import Chroma
from langchain_core.documents import Document

from rag.embedder import get_embeddings

# ChromaDB 持久化路径
CHROMA_PERSIST_DIR = str(Path(__file__).parent.parent.parent / "chroma_db")
KNOWLEDGE_BASE_DIR = str(Path(__file__).parent.parent.parent / "knowledge_base")

COLLECTION_RAG = "sleep_knowledge"        # RAG 知识库集合
COLLECTION_SEMANTIC = "user_semantic"     # 用户语义画像集合（Phase 2）


def ingest_knowledge_base() -> None:
    """
    扫描 knowledge_base/ 目录，将所有 .md / .txt 文档
    切片后向量化存入 ChromaDB sleep_knowledge 集合。
    """
    embeddings = get_embeddings()
    docs: list[Document] = []

    kb_path = Path(KNOWLEDGE_BASE_DIR)
    if not kb_path.exists():
        print(f"[Ingest] ⚠️  knowledge_base 目录不存在：{kb_path}")
        return

    for file_path in kb_path.rglob("*.md"):
        print(f"[Ingest] 📄 处理文件：{file_path.name}")
        text = file_path.read_text(encoding="utf-8")
        chunks = _split_markdown(text, source=file_path.name)
        docs.extend(chunks)

    for file_path in kb_path.rglob("*.txt"):
        print(f"[Ingest] 📄 处理文件：{file_path.name}")
        text = file_path.read_text(encoding="utf-8")
        chunks = _split_text(text, source=file_path.name)
        docs.extend(chunks)

    if not docs:
        print("[Ingest] ⚠️  没有找到任何文档")
        return

    print(f"[Ingest] ✂️  共切分为 {len(docs)} 个文档块，开始向量化...")

    vectorstore = Chroma.from_documents(
        documents=docs,
        embedding=embeddings,
        collection_name=COLLECTION_RAG,
        persist_directory=CHROMA_PERSIST_DIR,
    )

    print(f"[Ingest] ✅  成功存入 ChromaDB！路径：{CHROMA_PERSIST_DIR}")
    print(f"[Ingest] 📊  集合 '{COLLECTION_RAG}' 共 {vectorstore._collection.count()} 条向量")


def _split_markdown(text: str, source: str) -> list[Document]:
    """按 Markdown 标题层级切分文档"""
    headers_to_split_on = [
        ("#", "h1"),
        ("##", "h2"),
        ("###", "h3"),
    ]
    splitter = MarkdownHeaderTextSplitter(
        headers_to_split_on=headers_to_split_on,
        strip_headers=False,
    )
    md_docs = splitter.split_text(text)

    # 再按字符数二次切分（防止单节过长）
    char_splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=50,
    )
    chunks = char_splitter.split_documents(md_docs)

    for doc in chunks:
        doc.metadata["source"] = source
        doc.metadata["type"] = "knowledge"

    return chunks


def _split_text(text: str, source: str) -> list[Document]:
    """纯文本切分"""
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=50,
    )
    chunks = splitter.create_documents([text])
    for doc in chunks:
        doc.metadata["source"] = source
        doc.metadata["type"] = "knowledge"
    return chunks


if __name__ == "__main__":
    print("🚀 开始初始化 ChromaDB 知识库...")
    ingest_knowledge_base()
