"""
节点：action_executor
根据 Agent 推荐的 IoT 动作，调用 Mock 空调/日历 API 执行
"""
from __future__ import annotations

from agent.state import AgentState
from iot.ac_controller import set_ac_schedule, generate_default_ac_schedule
from iot.calendar_client import add_calendar_event, generate_sleep_reminders


def action_executor_node(state: AgentState) -> dict:
    """执行 Agent 推荐的 IoT 动作（同步，Mock 函数无需 async）"""
    actions = state.recommended_actions or []
    if not actions:
        return {}

    m = state.metrics or {}
    executed = []

    for action in actions:
        atype = action.get("type", "")

        if atype == "ac":
            schedule = generate_default_ac_schedule(state.date, state.user_id)
            result = set_ac_schedule(schedule)
            executed.append({
                "type": "ac",
                "success": result.success,
                "message": result.message,
                "details": [f"{s.time} → {s.temp}°C" for s in schedule.time_slots],
            })

        elif atype == "calendar":
            rem_low = m.get("rem_pct", 100) < 20
            eff_low = m.get("sleep_efficiency_pct", 100) < 85
            events = generate_sleep_reminders(state.user_id, state.date, rem_low, eff_low)
            for event in events:
                result = add_calendar_event(event)
                executed.append({
                    "type": "calendar",
                    "success": result.success,
                    "message": result.message,
                    "event_title": event.title,
                })

    return {"recommended_actions": executed}
