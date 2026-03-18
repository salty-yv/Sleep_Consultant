"""
节点4：memory_updater
分析完成后，将结果写回三层记忆：
  - PostgreSQL：更新 sleep_score 和 agent_report
  - ChromaDB：保存本次分析的关键发现作为语义记忆
  - Redis：保存 ReAct 推理轨迹
"""
from __future__ import annotations

from agent.state import AgentState
from memory.manager import memory_manager


def memory_updater_node(state: AgentState) -> dict:
    """
    分析完成后更新记忆系统。
    注意：PostgreSQL 的写回在 API 路由层用 async 完成，
    此节点主要负责 ChromaDB 语义记忆和 Redis 短期记忆。
    """
    # ── 保存 ReAct 推理轨迹到 Redis ──────────────
    session_id = f"{state.user_id}_{state.date}"
    if state.final_report:
        memory_manager.save_short_term(session_id, {
            "user_id": state.user_id,
            "date": state.date,
            "score": state.sleep_score,
            "report_preview": state.final_report[:200],
            "actions": state.recommended_actions,
        })

    # ── 提取本次关键发现，存入 ChromaDB 语义记忆 ──
    findings = _extract_findings(state)
    if findings:
        memory_manager.save_long_term(state.user_id, findings)

    return {}  # 不修改 state，只产生副作用


def _extract_findings(state: AgentState) -> str | None:
    """从分析报告中提取关键发现，作为语义记忆存储"""
    m = state.metrics or {}
    parts = []

    # 基于指标提取简短事实
    rem_pct = m.get("rem_pct", 0)
    deep_pct = m.get("deep_pct", 0)
    eff = m.get("sleep_efficiency_pct", 0)
    awakenings = m.get("awakening_count", 0)

    if rem_pct < 20:
        parts.append(f"{state.date} REM仅{rem_pct:.1f}%，低于标准")
    if deep_pct < 15:
        parts.append(f"{state.date} 深睡仅{deep_pct:.1f}%，偏低")
    if eff < 85:
        parts.append(f"{state.date} 睡眠效率{eff:.1f}%，不达标")
    if awakenings >= 4:
        parts.append(f"{state.date} 觉醒{awakenings}次，偏多")

    if state.sleep_score is not None:
        parts.append(f"{state.date} 睡眠评分{state.sleep_score}/100")

    return "；".join(parts) if parts else None
