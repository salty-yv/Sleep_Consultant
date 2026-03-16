"""
ORM 数据库表模型
"""
from __future__ import annotations

from datetime import datetime

from sqlalchemy import JSON, DateTime, Float, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from db.database import Base


class UserRecord(Base):
    """用户表"""
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(128), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class SleepRecord(Base):
    """睡眠记录表 - 存储每晚的 session + metrics"""
    __tablename__ = "sleep_records"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    date: Mapped[str] = mapped_column(String(10), nullable=False)   # YYYY-MM-DD
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    # 睡眠指标（冗余存储方便查询，不需要反序列化）
    total_record_min: Mapped[float] = mapped_column(Float, nullable=True)
    total_sleep_min: Mapped[float] = mapped_column(Float, nullable=True)
    rem_min: Mapped[float] = mapped_column(Float, nullable=True)
    deep_min: Mapped[float] = mapped_column(Float, nullable=True)
    light_min: Mapped[float] = mapped_column(Float, nullable=True)
    n1_min: Mapped[float] = mapped_column(Float, nullable=True)
    wake_min: Mapped[float] = mapped_column(Float, nullable=True)
    rem_pct: Mapped[float] = mapped_column(Float, nullable=True)
    deep_pct: Mapped[float] = mapped_column(Float, nullable=True)
    sleep_efficiency_pct: Mapped[float] = mapped_column(Float, nullable=True)
    sleep_cycle_count: Mapped[int] = mapped_column(Integer, nullable=True)
    awakening_count: Mapped[int] = mapped_column(Integer, nullable=True)
    avg_hr: Mapped[float] = mapped_column(Float, nullable=True)
    sleep_score: Mapped[int] = mapped_column(Integer, nullable=True)  # Agent 评分（后续 Phase）

    # 完整 JSON（epoch 列表 + 完整 metrics）
    epochs_json: Mapped[dict] = mapped_column(JSON, nullable=True)
    metrics_json: Mapped[dict] = mapped_column(JSON, nullable=True)
    agent_report: Mapped[str] = mapped_column(Text, nullable=True)   # Agent 分析文本（后续 Phase）
