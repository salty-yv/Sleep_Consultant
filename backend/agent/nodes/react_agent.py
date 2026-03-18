"""
节点3：react_agent
ReAct 推理核心：LLM Thought → Function Calling → Observation → 循环
Phase 1 基础版：使用 CoT Prompt + 5步结构化输出（无真实工具调用）
后续 Phase 会绑定 MCP 工具实现真正的 Function Calling
"""
from __future__ import annotations

import os
from langchain_core.messages import HumanMessage, SystemMessage

from agent.state import AgentState

# ── Prompt 版本化注册表 ─────────────────────────────────────
SYSTEM_PROMPT_V1 = """你是 SleepMind，一位基于循证医学的专业睡眠优化顾问。

【角色设定】
- 你的建议严格基于 AASM 睡眠医学指南和用户个人历史数据
- 你不做诊断，只提供生活方式干预建议
- 必要时主动建议使用工具（空调温控、日历提醒）

【输出格式约束】
- 分析过程必须按 5 步骤展示（CoT 格式）
- 每条建议必须附上依据（来自 RAG 知识库或历史规律）
- 最终报告结构：Step 1 Structure → Step 2 Root Cause → Step 3 Evidence → Step 4 Action → Step 5 Score
- 在 Step 5 末尾输出：SCORE: [数字]（0-100之间的整数）"""

COT_PROMPT_TEMPLATE_V2 = """【今晚睡眠数据】
{epochs_summary}

【该用户长期记忆（来自历史分析）】
{semantic_memories}

【相关医学知识（来自 AASM 知识库）】
{rag_docs}

【近7日趋势】
{weekly_trend}

---

【示例输出格式】
Step 1 / Structure:
  REM 占比 12%，低于标准 20-25%，深睡正常（18%）。

Step 2 / Root Cause:
  结合历史记忆——该用户周一至周五 REM 均低于周末，
  推测工作压力导致皮质醇偏高，抑制 REM 产生。

Step 3 / Evidence:
  AASM 指南：慢性压力是 REM 减少的首要原因之一。

Step 4 / Action:
  建议：将调用 add_sleep_calendar_event 添加明日 13:00 午休提醒。
  建议：将调用 set_ac_temperature_schedule 设置明晚深睡期 18-20°C 降温计划。

Step 5 / Score: 62/100
  主要扣分项：REM 严重不足（-25）、觉醒次数偏多（-13）。
  SCORE: 62

---

请按上述格式分析本次睡眠数据："""


PROMPT_REGISTRY = {
    "system_v1": SYSTEM_PROMPT_V1,
    "cot_v2": COT_PROMPT_TEMPLATE_V2,
}


def _format_trend(trend: list[dict]) -> str:
    if not trend:
        return "暂无历史趋势数据"
    lines = []
    for t in trend:
        lines.append(
            f"  {t.get('date','?')}：睡眠 {t.get('total_sleep_min','?'):.0f}分钟"
            f" | REM {t.get('rem_pct','?'):.1f}%"
            f" | 深睡 {t.get('deep_pct','?'):.1f}%"
            f" | 效率 {t.get('sleep_efficiency_pct','?'):.1f}%"
        )
    return "\n".join(lines)


def react_agent_node(state: AgentState) -> dict:
    """
    ReAct Agent 推理节点（Phase 1 基础版：CoT 5步结构输出）
    Phase 2+ 将绑定 MCP 工具，开启真正的 Function Calling 循环
    """
    # 构造 Prompt
    rag_docs_text = "\n\n".join(state.rag_docs or ["暂无相关医学知识"])
    trend_text = _format_trend(state.weekly_trend or [])

    cot_prompt = PROMPT_REGISTRY["cot_v2"].format(
        epochs_summary=state.epochs_summary or "无数据",
        semantic_memories=state.semantic_memories or "暂无长期记忆",
        rag_docs=rag_docs_text,
        weekly_trend=trend_text,
    )

    messages = [
        SystemMessage(content=PROMPT_REGISTRY["system_v1"]),
        HumanMessage(content=cot_prompt),
    ]

    # 调用 LLM
    llm = _get_llm()
    response = llm.invoke(messages)
    content = response.content

    # 提取评分
    score = _extract_score(content)

    # 提取建议动作
    actions = _extract_actions(content)

    return {
        "messages": [response],
        "final_report": content,
        "sleep_score": score,
        "recommended_actions": actions,
    }


def _get_llm():
    """获取 LLM（使用 AIHubMix 代理，从 config 读取配置）"""
    from core.config import settings

    api_key = settings.OPENAI_API_KEY
    if api_key and api_key not in ("", "你的AIHubMix-API-Key"):
        from langchain_openai import ChatOpenAI
        return ChatOpenAI(
            model=settings.OPENAI_MODEL,         # 默认 gpt-4o-mini
            temperature=0.3,
            openai_api_key=api_key,
            openai_api_base=settings.OPENAI_API_BASE,  # https://aihubmix.com/v1
        )
    else:
        # Mock LLM（无需 API Key，Phase 1 开发测试用）
        from langchain_core.language_models.fake import FakeListChatModel
        mock_report = """Step 1 / Structure:
  【Mock分析】REM 占比低于标准，深睡基本正常。

Step 2 / Root Cause:
  暂无历史记忆数据，推测可能与作息不规律有关。

Step 3 / Evidence:
  AASM 指南：慢性压力是 REM 减少的首要原因之一。规律作息可显著改善 REM 质量。

Step 4 / Action:
  建议：在设置 OpenAI API Key 后，Agent 将自动调用工具添加日历提醒和温控计划。

Step 5 / Score: 65/100
  当前为开发模式（Mock LLM），请设置 OPENAI_API_KEY 获取真实分析。
  SCORE: 65"""
        return FakeListChatModel(responses=[mock_report])


def _extract_score(text: str) -> int | None:
    """从报告中提取 SCORE: [数字]"""
    import re
    match = re.search(r"SCORE:\s*(\d+)", text)
    if match:
        return min(100, max(0, int(match.group(1))))
    return None


def _extract_actions(text: str) -> list[dict]:
    """从报告文本中提取推荐的 IoT 动作"""
    actions = []
    text_lower = text.lower()
    if "calendar" in text_lower or "日历" in text:
        actions.append({"type": "calendar", "description": "添加睡眠提醒到日历"})
    if "ac" in text_lower or "空调" in text or "温控" in text:
        actions.append({"type": "ac", "description": "设置明晚空调温控计划"})
    return actions
