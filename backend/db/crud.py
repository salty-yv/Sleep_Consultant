"""
CRUD 操作函数
"""
from __future__ import annotations

from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession

from db.orm_models import SleepRecord, UserRecord
from models.sleep_session import SleepMetrics, SleepSession


async def upsert_user(db: AsyncSession, user_id: str) -> UserRecord:
    """如果用户不存在则创建"""
    result = await db.execute(select(UserRecord).where(UserRecord.user_id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        user = UserRecord(user_id=user_id)
        db.add(user)
        await db.flush()
    return user


async def create_sleep_record(
    db: AsyncSession,
    session: SleepSession,
    metrics: SleepMetrics,
) -> SleepRecord:
    """保存一条睡眠记录到数据库"""
    record = SleepRecord(
        user_id=session.user_id,
        date=session.date,
        total_record_min=metrics.total_record_min,
        total_sleep_min=metrics.total_sleep_min,
        rem_min=metrics.rem_min,
        deep_min=metrics.deep_min,
        light_min=metrics.light_min,
        n1_min=metrics.n1_min,
        wake_min=metrics.wake_min,
        rem_pct=metrics.rem_pct,
        deep_pct=metrics.deep_pct,
        sleep_efficiency_pct=metrics.sleep_efficiency_pct,
        sleep_cycle_count=metrics.sleep_cycle_count,
        awakening_count=metrics.awakening_count,
        avg_hr=metrics.avg_hr,
        # 保存完整 JSON 供前端使用
        epochs_json=[ep.model_dump() for ep in session.epochs],
        metrics_json=metrics.model_dump(),
    )
    db.add(record)
    await db.flush()
    await db.refresh(record)
    return record


async def get_user_history(
    db: AsyncSession,
    user_id: str,
    limit: int = 30,
) -> list[SleepRecord]:
    """获取用户历史记录（按日期降序，默认最近30条）"""
    result = await db.execute(
        select(SleepRecord)
        .where(SleepRecord.user_id == user_id)
        .order_by(desc(SleepRecord.date))
        .limit(limit)
    )
    return list(result.scalars().all())


async def get_weekly_trend(
    db: AsyncSession,
    user_id: str,
) -> list[dict]:
    """获取最近7天的趋势数据（供 Agent 使用）"""
    records = await get_user_history(db, user_id, limit=7)
    trend = []
    for r in records:
        trend.append({
            "date": r.date,
            "total_sleep_min": r.total_sleep_min,
            "rem_pct": r.rem_pct,
            "deep_pct": r.deep_pct,
            "sleep_efficiency_pct": r.sleep_efficiency_pct,
            "awakening_count": r.awakening_count,
            "sleep_score": r.sleep_score,
        })
    return trend
