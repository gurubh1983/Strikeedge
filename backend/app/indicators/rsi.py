from __future__ import annotations

from app.domain.indicators import rsi as _rsi


def calculate_rsi(values: list[float], period: int = 14) -> float | None:
    return _rsi(values, period=period)
