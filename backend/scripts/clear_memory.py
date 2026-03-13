import asyncio
import json
import os
import shutil
import sys
from pathlib import Path

# 把 backend 根目录加到 sys.path
sys.path.append(str(Path(__file__).parent.parent))

from core.config import settings
from db.database import engine, Base
import db.orm_models  # noqa: F401  ← 必须导入，让 Base.metadata 注册表模型
from memory.redis_store import redis_store
from rag.ingest import CHROMA_PERSIST_DIR

async def clear_all_memory():
    print("🧹 开始清除所有记忆和缓存...")

    # 1. 清除 Redis 短期记忆
    if redis_store.connected:
        print("▶️ 正在清空 Redis 短期记忆...")
        redis_store._client.flushdb()
        print("✅ Redis 已清空")
    else:
        print("⚠️ 未连接到 Redis，跳过清空")

    # 2. 清除 ChromaDB 长期语义记忆和 RAG 知识库
    # 我们直接删除整个 chroma_db 文件夹，启动应用时会自动重新创建
    chroma_path = Path(CHROMA_PERSIST_DIR)
    if chroma_path.exists():
        print(f"▶️ 正在删除 ChromaDB 向量数据库 ({chroma_path})...")
        try:
            # 尝试删除目录
            shutil.rmtree(chroma_path)
            print("✅ ChromaDB 已删除 (下次启动将重新初始化)")
        except Exception as e:
            print(f"❌ 删除 ChromaDB 失败: {e}")
            print("   请确保没有其他进程（如 FastAPI 服务）正在占用这些文件。您可能需要先停止后端服务。")
    else:
        print("✅ 未找到 ChromaDB 目录，无需清除")

    # 3. 清除 PostgreSQL 中期情节记忆 (Sleep记录)
    print("▶️ 正在清空 PostgreSQL 数据库表...")
    try:
        async with engine.begin() as conn:
            # Drop all tables and recreate them
            await conn.run_sync(Base.metadata.drop_all)
            await conn.run_sync(Base.metadata.create_all)
        print("✅ PostgreSQL 睡眠记录和用户表已清空")
    except Exception as e:
        print(f"❌ 清空 PostgreSQL 失败: {e}")
        print("   请确保数据库连接正常。")

    print("\n🎉 清理完成！")
    print("⚠️ 提示：由于清空了数据库，您的所有用户数据已经丢失。")
    print("         由于清空了 ChromaDB，您可能需要重新运行知识库初始化脚本注入医学知识。")

if __name__ == "__main__":
    confirm = input("⚠️ 警告：这将删除所有用户的所有的睡眠记录、Redis缓存和ChromaDB记忆池！确定继续吗？(y/N): ")
    if confirm.lower() == 'y':
        asyncio.run(clear_all_memory())
    else:
        print("已取消清理。")
