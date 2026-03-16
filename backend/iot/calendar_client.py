"""
Mock 日历客户端（模拟 Google Calendar API）
Phase 3 IoT 执行层 - 用 Faker 数据代替真实 OAuth2 + Calendar API

真实场景中会调用 Google Calendar API v3：
  service.events().insert(calendarId='primary', body={...})
"""
from __future__ import annotations

from datetime import datetime
from pydantic import BaseModel, Field


class CalendarEvent(BaseModel):
    user_id: str
    event_type: str = Field(..., description="事件类型：bedtime/nap/reminder")
    title: str = Field(..., description="事件标题")
    start_time: str = Field(..., description="开始时间 ISO 格式")
    end_time: str = Field(..., description="结束时间 ISO 格式")
    description: str = Field("", description="事件描述 / Agent 推理理由")


class CalendarEventResult(BaseModel):
    success: bool
    event: CalendarEvent
    calendar_event_id: str  # Mock 的 Google Calendar event ID
    message: str
    created_at: str


# Mock 数据存储（内存）
_calendar_events: list[CalendarEventResult] = []
_event_counter = 0


def add_calendar_event(event: CalendarEvent) -> CalendarEventResult:
    """
    [Mock] 在 Google Calendar 创建事件。
    真实版本会通过 OAuth2 + Google Calendar API v3 插入。
    """
    global _event_counter
    _event_counter += 1
    mock_event_id = f"mock_event_{_event_counter:04d}"

    result = CalendarEventResult(
        success=True,
        event=event,
        calendar_event_id=mock_event_id,
        message=f"[Mock] ✅ 已在日历创建「{event.title}」事件",
        created_at=datetime.now().isoformat(),
    )
    _calendar_events.append(result)

    emoji = {"bedtime": "🛏️", "nap": "😴", "reminder": "⏰"}.get(event.event_type, "📅")
    print(f"[Calendar Mock] {emoji} 事件已创建：{event.title}")
    print(f"  时间：{event.start_time} → {event.end_time}")
    print(f"  说明：{event.description[:80]}")
    return result


def generate_sleep_reminders(
    user_id: str,
    date: str,
    rem_low: bool = False,
    efficiency_low: bool = False,
) -> list[CalendarEvent]:
    """根据 Agent 分析结果生成日历提醒事件"""
    events = []

    # 就寝提醒（每次都创建）
    events.append(CalendarEvent(
        user_id=user_id,
        event_type="bedtime",
        title="🌙 就寝时间",
        start_time=f"{date}T22:30:00",
        end_time=f"{date}T22:45:00",
        description="SleepMind 建议：建立固定作息节律，22:30 开始睡前准备",
    ))

    # REM 不足 → 午休提醒
    if rem_low:
        events.append(CalendarEvent(
            user_id=user_id,
            event_type="nap",
            title="😴 午休提醒（20分钟）",
            start_time=f"{date}T13:00:00",
            end_time=f"{date}T13:20:00",
            description="SleepMind 建议：昨晚 REM 不足，午休 20 分钟可部分补充",
        ))

    # 效率低 → 行为提醒
    if efficiency_low:
        events.append(CalendarEvent(
            user_id=user_id,
            event_type="reminder",
            title="⏰ 睡前提醒：20:00 后避免咖啡因",
            start_time=f"{date}T20:00:00",
            end_time=f"{date}T20:15:00",
            description="SleepMind 建议：咖啡因半衰期 5-6h，20:00 后停止摄入",
        ))

    return events


def get_calendar_history() -> list[CalendarEventResult]:
    """获取日历事件创建历史"""
    return _calendar_events
