"""
Embedder - 文本向量化模块
使用 OpenAI text-embedding-3-small（通过 AIHubMix 代理）
余额不足或网络错误时自动回退到 FakeEmbeddings
"""
from __future__ import annotations


def get_embeddings():
    """
    获取 Embedding 模型。
    - 如果设置了 OPENAI_API_KEY，通过 AIHubMix 代理使用 OpenAI embedding
    - API 调用失败（余额不足/网络错误）时自动回退到 FakeEmbeddings
    - 未设置 Key 时直接使用 FakeEmbeddings
    """
    from core.config import settings

    api_key = settings.OPENAI_API_KEY
    if api_key and api_key not in ("", "你的AIHubMix-API-Key"):
        try:
            from langchain_openai import OpenAIEmbeddings
            emb = OpenAIEmbeddings(
                model="text-embedding-3-small",
                openai_api_key=api_key,
                openai_api_base=settings.OPENAI_API_BASE,
            )
            # 快速验证一次：用短文本测试 API 是否可用
            emb.embed_query("test")
            print("[Embedder] ✅ OpenAI Embeddings 连接成功（AIHubMix）")
            return emb
        except Exception as e:
            print(f"[Embedder] ⚠️  OpenAI Embeddings 调用失败：{e}")
            print("[Embedder] ⚠️  自动回退到 FakeEmbeddings（本地开发模式）")

    # Fallback：FakeEmbeddings
    from langchain_community.embeddings import FakeEmbeddings
    print("[Embedder] 📌 使用 FakeEmbeddings（1536维，仅供开发测试）")
    return FakeEmbeddings(size=1536)

