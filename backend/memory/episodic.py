"""
情节记忆管理（PostgreSQL）
负责每晚分析后的记忆写回 + 历史趋势查询
"""
from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession
from db.crud import create_sleep_record, get_weekly_trend


async def save_episodic_memory(
    db: AsyncSession,
    session,
    metrics,
    agent_report: str | None = None,
    sleep_score: int | None = None,
) -> int:
    """
    保存一次分析的情节记忆到 PostgreSQL。
    返回 record_id。
    """
    record = await create_sleep_record(db, session, metrics)
    if agent_report or sleep_score is not None:
        from sqlalchemy import update
        from db.orm_models import SleepRecord
        await db.execute(
            update(SleepRecord)
            .where(SleepRecord.id == record.id)
            .values(
                agent_report=agent_report,
                sleep_score=sleep_score,
            )
        )
    return record.id


async def get_episodic_trend(db: AsyncSession, user_id: str) -> list[dict]:
    """获取近 7 日情节记忆趋势"""
    return await get_weekly_trend(db, user_id)
