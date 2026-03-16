"""
睡眠指标计算模块

AASM 标准参照：
  REM:  20-25% of total sleep
  Deep: 15-20% of total sleep
  Sleep Efficiency: > 85%
"""
from __future__ import annotations

from models.sleep_session import SleepEpoch, SleepMetrics, SleepSession

EPOCH_DURATION_MIN = 0.5  # 每个 epoch = 30 秒 = 0.5 分钟
CYCLE_DURATION_MIN = 90.0  # 每个睡眠周期约 90 分钟


def compute_metrics(session: SleepSession) -> SleepMetrics:
    """
    根据 SleepSession 计算所有睡眠统计指标。
    """
    epochs = session.epochs
    if not epochs:
        raise ValueError("SleepSession 中没有 epoch 数据")

    # ── 按阶段统计 epoch 数 ────────────────────────────────
    stage_counts: dict[str, int] = {
        "Wake": 0, "REM": 0, "N1": 0, "Light": 0, "Deep": 0
    }
    hr_values: list[float] = []

    for ep in epochs:
        stage = ep.stage_name or "Wake"
        stage_counts[stage] = stage_counts.get(stage, 0) + 1
        if ep.mean_hr is not None:
            hr_values.append(ep.mean_hr)

    # ── 转换为分钟 ─────────────────────────────────────────
    def to_min(count: int) -> float:
        return round(count * EPOCH_DURATION_MIN, 2)

    wake_min  = to_min(stage_counts.get("Wake", 0))
    rem_min   = to_min(stage_counts.get("REM", 0))
    n1_min    = to_min(stage_counts.get("N1", 0))
    light_min = to_min(stage_counts.get("Light", 0))
    deep_min  = to_min(stage_counts.get("Deep", 0))

    total_record_min = round(len(epochs) * EPOCH_DURATION_MIN, 2)
    total_sleep_min  = round(rem_min + n1_min + light_min + deep_min, 2)

    # ── 百分比 ─────────────────────────────────────────────
    def pct(val: float, base: float) -> float:
        return round(val / base * 100, 1) if base > 0 else 0.0

    rem_pct   = pct(rem_min, total_sleep_min)
    n1_pct    = pct(n1_min, total_sleep_min)
    light_pct = pct(light_min, total_sleep_min)
    deep_pct  = pct(deep_min, total_sleep_min)
    wake_pct  = pct(wake_min, total_record_min)

    # ── 睡眠效率 ───────────────────────────────────────────
    sleep_efficiency_pct = pct(total_sleep_min, total_record_min)

    # ── 睡眠周期数（粗估：总睡眠 / 90min）─────────────────
    sleep_cycle_count = max(0, int(total_sleep_min // CYCLE_DURATION_MIN))

    # ── 觉醒次数（连续 Wake 段算一次）─────────────────────
    awakening_count = _count_awakenings(epochs)

    # ── 平均心率 ───────────────────────────────────────────
    avg_hr = round(sum(hr_values) / len(hr_values), 1) if hr_values else None

    # ── AASM 标准对比 ──────────────────────────────────────
    rem_vs_standard  = _compare(rem_pct, 20.0, 25.0)
    deep_vs_standard = _compare(deep_pct, 15.0, 20.0)
    efficiency_vs_standard = 1 if sleep_efficiency_pct >= 85.0 else -1

    return SleepMetrics(
        user_id=session.user_id,
        date=session.date,
        total_record_min=total_record_min,
        total_sleep_min=total_sleep_min,
        wake_min=wake_min,
        rem_min=rem_min,
        n1_min=n1_min,
        light_min=light_min,
        deep_min=deep_min,
        rem_pct=rem_pct,
        n1_pct=n1_pct,
        light_pct=light_pct,
        deep_pct=deep_pct,
        wake_pct=wake_pct,
        sleep_efficiency_pct=sleep_efficiency_pct,
        sleep_cycle_count=sleep_cycle_count,
        awakening_count=awakening_count,
        avg_hr=avg_hr,
        rem_vs_standard=rem_vs_standard,
        deep_vs_standard=deep_vs_standard,
        efficiency_vs_standard=efficiency_vs_standard,
    )


def _count_awakenings(epochs: list[SleepEpoch]) -> int:
    """统计觉醒次数：连续的 Wake epoch 段计为一次觉醒。"""
    count = 0
    in_wake_segment = False
    for ep in epochs:
        is_wake = (ep.stage_name == "Wake" or ep.stage_name is None)
        if is_wake and not in_wake_segment:
            count += 1
            in_wake_segment = True
        elif not is_wake:
            in_wake_segment = False
    return count


def _compare(value: float, low: float, high: float) -> int:
    """对比某个指标是否在范围内：1=偏高, 0=正常, -1=偏低"""
    if value < low:
        return -1
    elif value > high:
        return 1
    return 0
