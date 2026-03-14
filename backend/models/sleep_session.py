"""
Pydantic Schema 定义 - 睡眠数据模型

pred_stage_code 对照表：
  1 = Wake    (清醒)
  2 = REM     (快速眼动)
  3 = Light   (浅睡 N2)
  4 = Deep    (深睡 N3)
  5 = N1      (入睡过渡)
"""
from __future__ import annotations

from datetime import date as DateType
from typing import Optional
from pydantic import BaseModel, Field


# ── 睡眠阶段枚举 ────────────────────────────────────────────
STAGE_CODE_MAP: dict[int, str] = {
    1: "Wake",
    2: "REM",
    3: "Light",   # N2
    4: "Deep",    # N3
    5: "N1",      # 入睡过渡
}

SLEEP_STAGES = {"REM", "Light", "Deep", "N1"}  # 非 Wake 阶段视为睡眠


# ── 单个 Epoch ──────────────────────────────────────────────
class SleepEpoch(BaseModel):
    epoch_start_sec: int = Field(..., description="从第一次记录到该 epoch 开始的秒数")
    mean_hr: Optional[float] = Field(None, description="该 epoch 平均心率 (bpm)")
    elapsed_hours: float = Field(..., description="经过小时数")
    progress: float = Field(..., description="进度 0-1")
    stage_code: Optional[int] = Field(None, description="睡眠阶段代码 1-5，None 表示无法识别")
    stage_name: Optional[str] = Field(None, description="睡眠阶段名称")

    @classmethod
    def from_csv_row(cls, row: dict) -> "SleepEpoch":
        code_raw = row.get("pred_stage_code")
        if code_raw is None or (isinstance(code_raw, float) and __import__("math").isnan(code_raw)):
            code = None
        else:
            code = int(code_raw)
        return cls(
            epoch_start_sec=int(row["epoch_start_sec"]),
            mean_hr=float(row["mean_hr"]) if row.get("mean_hr") else None,
            elapsed_hours=float(row["elapsed_hours"]),
            progress=float(row["progress"]),
            stage_code=code,
            stage_name=STAGE_CODE_MAP.get(code) if code is not None else "Wake",
        )


# ── 完整睡眠 Session ────────────────────────────────────────
class SleepSession(BaseModel):
    user_id: str = Field(..., description="用户 ID")
    date: str = Field(..., description="睡眠日期（YYYY-MM-DD），通常为翌日早晨")
    epochs: list[SleepEpoch] = Field(default_factory=list, description="所有 epoch 列表")
    total_epochs: int = Field(0, description="总 epoch 数")
    total_duration_min: float = Field(0.0, description="总记录时长（分钟）")

    def model_post_init(self, __context) -> None:
        self.total_epochs = len(self.epochs)
        if self.epochs:
            last_epoch = self.epochs[-1]
            self.total_duration_min = (last_epoch.epoch_start_sec + 30) / 60.0


# ── 计算后的统计指标 ────────────────────────────────────────
class SleepMetrics(BaseModel):
    user_id: str
    date: str

    # 时长指标（分钟）
    total_record_min: float = Field(..., description="总记录时长（分钟）")
    total_sleep_min: float = Field(..., description="实际睡眠时长（非Wake）分钟")
    wake_min: float = Field(..., description="清醒时长（分钟）")
    rem_min: float = Field(..., description="REM 时长（分钟）")
    n1_min: float = Field(..., description="N1 浅睡时长（分钟）")
    light_min: float = Field(..., description="Light(N2) 时长（分钟）")
    deep_min: float = Field(..., description="Deep(N3) 时长（分钟）")

    # 占比指标（%，基于总睡眠时长）
    rem_pct: float = Field(..., description="REM 占睡眠时长百分比")
    n1_pct: float = Field(..., description="N1 占睡眠时长百分比")
    light_pct: float = Field(..., description="Light 占睡眠时长百分比")
    deep_pct: float = Field(..., description="Deep 占睡眠时长百分比")
    wake_pct: float = Field(..., description="Wake 占总记录时长百分比")

    # 质量指标
    sleep_efficiency_pct: float = Field(..., description="睡眠效率 = 睡眠时长/总记录时长 × 100")
    sleep_cycle_count: int = Field(..., description="估算的完整睡眠周期数（~90min/周期）")
    awakening_count: int = Field(..., description="觉醒次数（连续 Wake 段计为一次）")
    avg_hr: Optional[float] = Field(None, description="全程平均心率")

    # AASM 标准对比（0=达标，1=偏高，-1=偏低）
    rem_vs_standard: int = Field(..., description="REM对比标准(20-25%): 1偏高 0达标 -1偏低")
    deep_vs_standard: int = Field(..., description="Deep对比标准(15-20%): 1偏高 0达标 -1偏低")
    efficiency_vs_standard: int = Field(..., description="效率对比标准(>85%): 1达标 -1偏低")


# ── 完整分析报告（Session + Metrics）──────────────────────
class SleepReport(BaseModel):
    session: SleepSession
    metrics: SleepMetrics
    agent_analysis: Optional[str] = Field(None, description="Agent 分析文本（Phase 1 暂留空）")
    sleep_score: Optional[int] = Field(None, description="睡眠综合评分 0-100（Phase 1 暂留空）")


# ── 上传请求 / 响应 ─────────────────────────────────────────
class UploadSleepResponse(BaseModel):
    success: bool
    record_id: int
    user_id: str
    date: str
    metrics: SleepMetrics
    message: str


class HistoryResponse(BaseModel):
    user_id: str
    records: list[dict]
    total_count: int
