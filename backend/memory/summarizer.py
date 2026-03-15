"""
记忆压缩摘要器
使用 LLM 将本周睡眠数据规律压缩为简洁的语义记忆，存入 ChromaDB
由 APScheduler 每周定时任务触发
"""
from __future__ import annotations

import os


async def compress_weekly_memories(user_id: str, weekly_records: list[dict]) -> str:
    """
    将一周的睡眠记录通过 LLM 压缩为语义摘要。

    Args:
        user_id: 用户 ID
        weekly_records: 7天的 metrics 数据列表

    Returns:
        压缩后的语义记忆文本
    """
    if not weekly_records:
        return ""

    # 构造 LLM 输入
    records_text = "\n".join(
        f"  {r.get('date','?')}: 睡眠{r.get('total_sleep_min',0):.0f}分钟 "
        f"REM{r.get('rem_pct',0):.1f}% 深睡{r.get('deep_pct',0):.1f}% "
        f"效率{r.get('sleep_efficiency_pct',0):.1f}% 觉醒{r.get('awakening_count',0)}次"
        for r in weekly_records
    )

    prompt = f"""请分析以下用户一周的睡眠数据，提炼出 2-3 条关键规律，用简洁的语句描述。
只输出规律本身，不要客套话。

用户 {user_id} 本周数据：
{records_text}

输出格式示例：
- 工作日 REM 占比低于周末，平均差 5%
- 觉醒次数与深睡呈负相关
- 睡眠效率在 85% 左右徘徊"""

    llm = _get_llm()
    from langchain_core.messages import HumanMessage, SystemMessage
    response = await llm.ainvoke([
        SystemMessage(content="你是一个睡眠数据分析专家，负责从历史数据中提炼用户的睡眠规律和特征。"),
        HumanMessage(content=prompt),
    ])
    return response.content


def _get_llm():
    from core.config import settings
    api_key = settings.OPENAI_API_KEY
    if api_key and api_key not in ("", "你的AIHubMix-API-Key"):
        from langchain_openai import ChatOpenAI
        return ChatOpenAI(
            model=settings.OPENAI_MODEL,
            temperature=0.3,
            openai_api_key=api_key,
            openai_api_base=settings.OPENAI_API_BASE,
        )
    else:
        from langchain_core.language_models.fake import FakeListChatModel
        return FakeListChatModel(responses=[
            "- 本周睡眠效率整体偏低，REM 占比不足\n- 觉醒次数较多，可能与环境噪音有关\n- 深睡集中在前半夜，后半夜碎片化严重"
        ])
