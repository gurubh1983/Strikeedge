from __future__ import annotations

from app.indicators.macd import calculate_macd
from app.indicators.rsi import calculate_rsi


def test_rsi_calculation() -> None:
    closes = [100 + i for i in range(30)]
    value = calculate_rsi(closes, period=14)
    assert value is not None
    assert 0 <= value <= 100


def test_macd_and_histogram() -> None:
    closes = [100 + (i * 0.5) for i in range(60)]
    macd_line, signal_line, histogram = calculate_macd(closes)
    assert macd_line is not None
    assert signal_line is not None
    assert histogram is not None
