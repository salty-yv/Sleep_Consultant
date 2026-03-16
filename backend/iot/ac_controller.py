"""
Mock 空调控制器（模拟 Home Assistant API）
Phase 3 IoT 执行层 - 用 Faker 数据代替真实 API 调用

真实场景中会调用 Home Assistant REST API：
  POST /api/services/climate/set_temperature
  {"entity_id": "climate.bedroom_ac", "temperature": 20}
"""
from __future__ import annotations

import random
from datetime import datetime
from pydantic import BaseModel, Field


class AcTimeSlot(BaseModel):
    time: str = Field(..., description="时间 HH:MM")
    temp: float = Field(..., description="目标温度 °C")
    reason: str = Field("", description="设定理由")


class AcSchedule(BaseModel):
    user_id: str
    date: str
    time_slots: list[AcTimeSlot] = Field(default_factory=list)


class AcExecutionResult(BaseModel):
    success: bool
    schedule: AcSchedule
    message: str
    executed_at: str


# Mock 数据存储（内存）
_ac_history: list[AcExecutionResult] = []


def set_ac_schedule(schedule: AcSchedule) -> AcExecutionResult:
    """
    [Mock] 向 Home Assistant 下发温控计划。
    真实版本会通过 HA REST API 调用 climate.set_temperature。
    """
    # 模拟 API 调用延迟和结果
    result = AcExecutionResult(
        success=True,
        schedule=schedule,
        message=f"[Mock] ✅ 已设定 {len(schedule.time_slots)} 个温控时段",
        executed_at=datetime.now().isoformat(),
    )
    _ac_history.append(result)
    print(f"[AC Mock] 📋 温控计划已下发给 Home Assistant（模拟）：")
    for slot in schedule.time_slots:
        print(f"  {slot.time} → {slot.temp}°C  ({slot.reason})")
    return result


def generate_default_ac_schedule(date: str, user_id: str) -> AcSchedule:
    """
    根据 AASM 建议生成默认温控计划。
    真实版本会根据 Agent 对睡眠阶段的预测动态生成。
    """
    return AcSchedule(
        user_id=user_id,
        date=date,
        time_slots=[
            AcTimeSlot(time="22:00", temp=26.0, reason="入睡前保持舒适温度"),
            AcTimeSlot(time="23:00", temp=20.0, reason="深睡期降温促进 N3"),
            AcTimeSlot(time="02:00", temp=22.0, reason="REM 期体温调节能力弱，略升温"),
            AcTimeSlot(time="06:00", temp=24.0, reason="模拟自然升温，柔和唤醒"),
        ],
    )


def get_ac_history() -> list[AcExecutionResult]:
    """获取空调执行历史"""
    return _ac_history
