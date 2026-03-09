from __future__ import annotations

from app.domain.indicators import macd as _macd


def calculate_macd(values: list[float]) -> tuple[float | None, float | None, float | None]:
    macd_line, signal_line = _macd(values)
    if macd_line is None or signal_line is None:
        return None, None, None
    histogram = macd_line - signal_line
    return macd_line, signal_line, histogram
