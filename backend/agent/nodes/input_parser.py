"""
节点1：input_parser
解析睡眠数据，构造供 LLM 阅读的摘要文本，识别主要问题
"""
from __future__ import annotations

from agent.state import AgentState


# AASM 参考标准（用于生成提示文本）
AASM_STANDARDS = {
    "rem_pct":             (20.0, 25.0),
    "deep_pct":            (15.0, 20.0),
    "sleep_efficiency_pct": (85.0, 100.0),
}


def input_parser_node(state: AgentState) -> dict:
    """
    从 state.metrics 中读取计算好的指标，
    生成可供 LLM 理解的文本摘要，存入 state.epochs_summary
    """
    m = state.metrics
    if not m:
        return {"epochs_summary": "⚠️  未提供睡眠数据"}

    # 生成人类可读摘要
    lines = [
        f"📅 日期：{state.date}",
        f"⏱️  总记录时长：{m.get('total_record_min', 0):.0f} 分钟",
        f"😴 实际睡眠：{m.get('total_sleep_min', 0):.0f} 分钟",
        "",
        "【睡眠结构】",
        f"  REM   ：{m.get('rem_min', 0):.0f}分钟 / {m.get('rem_pct', 0):.1f}%  （AASM标准 20-25%）",
        f"  深睡N3：{m.get('deep_min', 0):.0f}分钟 / {m.get('deep_pct', 0):.1f}%  （AASM标准 15-20%）",
        f"  浅睡N2：{m.get('light_min', 0):.0f}分钟 / {m.get('light_pct', 0):.1f}%",
        f"  N1    ：{m.get('n1_min', 0):.0f}分钟 / {m.get('n1_pct', 0):.1f}%",
        f"  清醒  ：{m.get('wake_min', 0):.0f}分钟 / {m.get('wake_pct', 0):.1f}%",
        "",
        "【质量指标】",
        f"  睡眠效率：{m.get('sleep_efficiency_pct', 0):.1f}%  （标准 > 85%）",
        f"  完整周期：{m.get('sleep_cycle_count', 0)} 个  （理想 4-6 个）",
        f"  觉醒次数：{m.get('awakening_count', 0)} 次",
        f"  平均心率：{m.get('avg_hr') or '未知'} bpm",
    ]

    # 标注问题
    issues = []
    rem_pct = m.get("rem_pct", 0)
    deep_pct = m.get("deep_pct", 0)
    eff = m.get("sleep_efficiency_pct", 0)

    if rem_pct < 20:
        issues.append(f"REM不足（{rem_pct:.1f}% < 20%）")
    elif rem_pct > 25:
        issues.append(f"REM偏多（{rem_pct:.1f}% > 25%）")
    if deep_pct < 15:
        issues.append(f"深睡不足（{deep_pct:.1f}% < 15%）")
    if eff < 85:
        issues.append(f"睡眠效率偏低（{eff:.1f}%）")
    if m.get("awakening_count", 0) >= 4:
        issues.append(f"觉醒次数偏多（{m.get('awakening_count')} 次）")

    if issues:
        lines.append("")
        lines.append("【识别到的主要问题】")
        for i, issue in enumerate(issues, 1):
            lines.append(f"  {i}. {issue}")
    else:
        lines.append("")
        lines.append("【睡眠结构良好，各项指标基本达标】")

    summary = "\n".join(lines)
    return {"epochs_summary": summary}
