from __future__ import annotations


def ema(values: list[float], period: int) -> float | None:
    if len(values) < period:
        return None
    multiplier = 2 / (period + 1)
    out = sum(values[:period]) / period
    for value in values[period:]:
        out = (value - out) * multiplier + out
    return out


def rsi(values: list[float], period: int = 14) -> float | None:
    if len(values) <= period:
        return None
    gains: list[float] = []
    losses: list[float] = []
    for idx in range(1, len(values)):
        delta = values[idx] - values[idx - 1]
        gains.append(max(delta, 0))
        losses.append(max(-delta, 0))
    avg_gain = sum(gains[:period]) / period
    avg_loss = sum(losses[:period]) / period
    if avg_loss == 0:
        return 100.0
    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))


def macd(values: list[float]) -> tuple[float | None, float | None]:
    if len(values) < 26:
        return None, None
    ema12 = ema(values, 12)
    ema26 = ema(values, 26)
    if ema12 is None or ema26 is None:
        return None, None
    macd_value = ema12 - ema26

    macd_series: list[float] = []
    for idx in range(26, len(values) + 1):
        window = values[:idx]
        e12 = ema(window, 12)
        e26 = ema(window, 26)
        if e12 is not None and e26 is not None:
            macd_series.append(e12 - e26)
    signal = ema(macd_series, 9) if macd_series else None
    return macd_value, signal
