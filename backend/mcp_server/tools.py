"""
MCP Server 工具注册
定义所有 Agent 可调用的工具 Schema（供 Function Calling 使用）

Phase 1: 工具以普通 Python 函数形式定义
Phase 3: 将迁移到真正的 MCP Server 注册
"""
from __future__ import annotations

from rag.retriever import search_sleep_knowledge, recall_user_memory
from iot.ac_controller import (
    AcSchedule, AcTimeSlot,
    set_ac_schedule, generate_default_ac_schedule,
)
from iot.calendar_client import (
    CalendarEvent,
    add_calendar_event, generate_sleep_reminders,
)


# ── 知识 & 分析工具 ─────────────────────────────────
async def tool_compute_sleep_score(rem_pct: float, deep_pct: float, efficiency: float) -> dict:
    """计算睡眠综合评分（0-100）"""
    score = 100
    # REM 评分
    if rem_pct < 20:
        score -= min(30, (20 - rem_pct) * 2)
    elif rem_pct > 25:
        score -= min(10, (rem_pct - 25) * 1)
    # Deep 评分
    if deep_pct < 15:
        score -= min(25, (15 - deep_pct) * 2)
    # 效率评分
    if efficiency < 85:
        score -= min(20, (85 - efficiency) * 1)
    return {"score": max(0, int(score)), "breakdown": {
        "rem_impact": round(max(0, 20 - rem_pct) * 2, 1) if rem_pct < 20 else 0,
        "deep_impact": round(max(0, 15 - deep_pct) * 2, 1) if deep_pct < 15 else 0,
        "efficiency_impact": round(max(0, 85 - efficiency), 1) if efficiency < 85 else 0,
    }}


async def tool_search_sleep_knowledge(query: str, top_k: int = 3) -> list[str]:
    """从 AASM 睡眠医学知识库检索相关内容"""
    return search_sleep_knowledge(query, top_k)


async def tool_get_sleep_guidelines(condition: str) -> str:
    """获取特定睡眠问题的指南建议"""
    docs = search_sleep_knowledge(condition, top_k=2)
    return "\n\n".join(docs) if docs else "未找到相关指南"


# ── 记忆工具 ────────────────────────────────────────
async def tool_recall_user_memory(user_id: str, query: str) -> str:
    """从长期记忆中检索与当前问题相关的用户历史规律"""
    return recall_user_memory(user_id, query)


# ── IoT 执行工具 ────────────────────────────────────
async def tool_set_ac_temperature_schedule(
    user_id: str, date: str,
    schedule: list[dict] | None = None,
) -> dict:
    """向 Home Assistant 下发明晚空调温控计划"""
    if schedule:
        ac_schedule = AcSchedule(
            user_id=user_id, date=date,
            time_slots=[AcTimeSlot(**s) for s in schedule],
        )
    else:
        ac_schedule = generate_default_ac_schedule(date, user_id)
    result = await set_ac_schedule(ac_schedule)
    return result.model_dump()


async def tool_add_sleep_calendar_event(
    user_id: str,
    event_type: str,
    title: str,
    start_time: str,
    end_time: str,
    description: str = "",
) -> dict:
    """在 Google Calendar 添加睡眠相关提醒事件"""
    event = CalendarEvent(
        user_id=user_id,
        event_type=event_type,
        title=title,
        start_time=start_time,
        end_time=end_time,
        description=description,
    )
    result = await add_calendar_event(event)
    return result.model_dump()


# ── 工具注册表（供 LangChain bind_tools 使用）────────
TOOL_REGISTRY = {
    "compute_sleep_score": tool_compute_sleep_score,
    "search_sleep_knowledge": tool_search_sleep_knowledge,
    "get_sleep_guidelines": tool_get_sleep_guidelines,
    "recall_user_memory": tool_recall_user_memory,
    "set_ac_temperature_schedule": tool_set_ac_temperature_schedule,
    "add_sleep_calendar_event": tool_add_sleep_calendar_event,
}
