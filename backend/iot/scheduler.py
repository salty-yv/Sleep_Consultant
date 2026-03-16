"""
IoT 定时调度器（APScheduler）
- 每周日凌晨 3 点执行记忆压缩任务
- 模拟版：同时可用于手动触发
"""
from __future__ import annotations

import asyncio
from datetime import datetime


# APScheduler 定时任务（简化版，不依赖 APScheduler 包）
_scheduled_tasks: list[dict] = []


async def run_weekly_memory_compression(user_id: str, db_session_factory) -> str:
    """
    每周定时任务：压缩本周睡眠记忆 → 更新 ChromaDB 语义画像。

    真实部署时由 APScheduler 定时触发：
      scheduler.add_job(run_weekly_memory_compression, 'cron',
                        day_of_week='sun', hour=3, args=[user_id, db_factory])
    """
    from memory.summarizer import compress_weekly_memories
    from memory.manager import memory_manager
    from db.crud import get_weekly_trend

    async with db_session_factory() as db:
        weekly_data = await get_weekly_trend(db, user_id)

    if not weekly_data:
        return f"[Scheduler] 用户 {user_id} 无本周数据，跳过压缩"

    # LLM 压缩本周数据为语义记忆
    summary = await compress_weekly_memories(user_id, weekly_data)

    # 存入 ChromaDB
    memory_manager.save_long_term(user_id, summary)

    result = f"[Scheduler] ✅ 用户 {user_id} 本周记忆已压缩并存入 ChromaDB"
    print(result)
    print(f"  摘要：{summary[:100]}...")

    _scheduled_tasks.append({
        "user_id": user_id,
        "type": "memory_compression",
        "executed_at": datetime.now().isoformat(),
        "summary_preview": summary[:100],
    })
    return result


def get_scheduler_history() -> list[dict]:
    """获取定时任务执行历史"""
    return _scheduled_tasks
