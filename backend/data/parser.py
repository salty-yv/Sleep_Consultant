"""
CSV 解析器 - 将 new_data_with_pred.csv 格式转换为 SleepSession
"""
from __future__ import annotations

import io
import math
from datetime import date as DateType

import pandas as pd

from models.sleep_session import SleepEpoch, SleepSession


def parse_csv_to_session(
    csv_source: bytes | str | io.IOBase | pd.DataFrame,
    user_id: str,
    date: str,
) -> SleepSession:
    """
    将 CSV 文件（字节/路径/DataFrame）解析为 SleepSession。

    Args:
        csv_source: CSV 原始字节、文件路径字符串或 DataFrame
        user_id:    用户 ID
        date:       睡眠日期（YYYY-MM-DD）

    Returns:
        SleepSession Pydantic 对象
    """
    if isinstance(csv_source, pd.DataFrame):
        df = csv_source
    elif isinstance(csv_source, bytes):
        df = pd.read_csv(io.BytesIO(csv_source))
    else:
        df = pd.read_csv(csv_source)

    _validate_columns(df)

    epochs: list[SleepEpoch] = []
    for _, row in df.iterrows():
        epoch = SleepEpoch.from_csv_row(row.to_dict())
        epochs.append(epoch)

    session = SleepSession(
        user_id=user_id,
        date=date,
        epochs=epochs,
    )
    return session


def _validate_columns(df: pd.DataFrame) -> None:
    required = {"epoch_start_sec", "elapsed_hours", "progress"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"CSV 缺少必要列：{missing}")
