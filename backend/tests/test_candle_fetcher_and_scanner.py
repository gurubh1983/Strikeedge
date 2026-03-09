from __future__ import annotations

import pandas as pd

from app.data_pipeline.candle_fetcher import CandleFetcher
from app.screener.scanner import ConditionGroup, IndicatorCondition, Scanner, evaluate_group, screen_rows


def test_to_dataframe() -> None:
    records = [
        {"timestamp": "2026-03-08T09:15:00Z", "open": 100, "high": 102, "low": 99, "close": 101, "volume": 200},
        {"timestamp": "2026-03-08T09:16:00Z", "open": 101, "high": 103, "low": 100, "close": 102, "volume": 300},
    ]
    frame = CandleFetcher.to_dataframe(records)
    assert isinstance(frame, pd.DataFrame)
    assert len(frame) == 2
    assert "close" in frame.columns


def test_support_1m() -> None:
    assert CandleFetcher.support_1m("1m") is True
    assert CandleFetcher.support_1m("5m") is False


def test_screen_rows() -> None:
    rows = [
        {"token": "A", "rsi_14": 65.0, "ema_20": 100.0},
        {"token": "B", "rsi_14": 40.0, "ema_20": 90.0},
    ]
    conditions = [IndicatorCondition(field="rsi_14", operator=">", value=60)]
    out = screen_rows(rows, conditions)
    assert len(out) == 1
    assert out[0]["token"] == "A"


def test_cross_above_condition_with_previous_values() -> None:
    rows = [{"token": "A", "rsi_14": 61.0}]
    previous_rows = {"A": {"rsi_14": 58.0}}
    conditions = [IndicatorCondition(field="rsi_14", operator="crosses_above", value=60)]
    out = screen_rows(rows, conditions, previous_rows=previous_rows)
    assert len(out) == 1


def test_condition_group_or() -> None:
    row = {"token": "A", "rsi_14": 45.0, "ema_20": 102.0}
    group = ConditionGroup(
        logical_operator="OR",
        conditions=[
            IndicatorCondition(field="rsi_14", operator=">", value=60),
            IndicatorCondition(field="ema_20", operator=">", value=100),
        ],
    )
    assert evaluate_group(row, None, group) is True


def test_scanner_class_run() -> None:
    scanner = Scanner(
        groups=[
            ConditionGroup(
                logical_operator="AND",
                conditions=[IndicatorCondition(field="ema_20", operator=">", value=100)],
            )
        ]
    )
    out = scanner.run([{"token": "A", "ema_20": 102.0}, {"token": "B", "ema_20": 95.0}])
    assert len(out) == 1
    assert out[0]["token"] == "A"
