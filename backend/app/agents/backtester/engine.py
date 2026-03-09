"""Backtest engine: historical candles → indicators → entry/exit → P&L, Sharpe, max drawdown."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from app.domain.indicators import ema, macd, rsi
from app.screener.scanner import ConditionGroup, IndicatorCondition, evaluate_group


@dataclass
class Trade:
    token: str
    entry_bar: int
    exit_bar: int
    entry_price: float
    exit_price: float
    pnl: float
    entry_reason: str
    exit_reason: str


def _compute_indicators(closes: list[float]) -> list[dict[str, Any]]:
    """Compute rsi_14, ema_20, macd, macd_signal for each bar (index = len(closes) - 1)."""
    result: list[dict[str, Any]] = []
    for i in range(len(closes)):
        window = closes[: i + 1]
        rsi_val = rsi(window, period=14) if len(window) > 14 else None
        ema_val = ema(window, period=20) if len(window) >= 20 else None
        macd_val, macd_sig = macd(window) if len(window) >= 26 else (None, None)
        result.append({
            "rsi_14": rsi_val,
            "ema_20": ema_val,
            "macd": macd_val,
            "macd_signal": macd_sig,
        })
    return result


def run_backtest(
    *,
    token: str,
    candles: list[dict[str, Any]],
    groups: list[ConditionGroup],
    hold_bars: int = 5,
    exit_rsi_high: float = 70.0,
    exit_rsi_low: float = 30.0,
) -> tuple[list[Trade], float, float, float, float]:
    """
    Run backtest on historical candles.
    Entry: when condition group passes. Exit: after hold_bars or when RSI crosses exit levels.
    Returns (trades, total_pnl, sharpe, max_drawdown, win_rate).
    """
    if len(candles) < 30:
        return [], 0.0, 0.0, 0.0, 0.0, 0

    closes = [float(c.get("close", 0)) for c in candles]
    indicators = _compute_indicators(closes)
    trades: list[Trade] = []
    in_position = False
    entry_bar = 0
    entry_price = 0.0
    entry_reason = ""

    for i in range(26, len(candles)):
        row = {
            "token": token,
            "rsi_14": indicators[i]["rsi_14"],
            "ema_20": indicators[i]["ema_20"],
            "macd": indicators[i]["macd"],
            "macd_signal": indicators[i]["macd_signal"],
        }
        prev_row = {
            "token": token,
            "rsi_14": indicators[i - 1]["rsi_14"],
            "ema_20": indicators[i - 1]["ema_20"],
            "macd": indicators[i - 1]["macd"],
            "macd_signal": indicators[i - 1]["macd_signal"],
        }

        if in_position:
            exit_reason = ""
            rsi_now = row.get("rsi_14")
            if rsi_now is not None:
                if rsi_now >= exit_rsi_high:
                    exit_reason = f"RSI>={exit_rsi_high}"
                elif rsi_now <= exit_rsi_low:
                    exit_reason = f"RSI<={exit_rsi_low}"
            if not exit_reason and (i - entry_bar) >= hold_bars:
                exit_reason = f"hold_{hold_bars}_bars"

            if exit_reason:
                exit_price = closes[i]
                pnl = exit_price - entry_price
                trades.append(
                    Trade(
                        token=token,
                        entry_bar=entry_bar,
                        exit_bar=i,
                        entry_price=entry_price,
                        exit_price=exit_price,
                        pnl=pnl,
                        entry_reason=entry_reason,
                        exit_reason=exit_reason,
                    )
                )
                in_position = False

        if not in_position and groups:
            if all(evaluate_group(row, prev_row, g) for g in groups):
                in_position = True
                entry_bar = i
                entry_price = closes[i]
                entry_reason = "rules"

    if in_position:
        exit_price = closes[-1]
        trades.append(
            Trade(
                token=token,
                entry_bar=entry_bar,
                exit_bar=len(candles) - 1,
                entry_price=entry_price,
                exit_price=exit_price,
                pnl=exit_price - entry_price,
                entry_reason=entry_reason,
                exit_reason="eot",
            )
        )

    total_pnl = sum(t.pnl for t in trades)
    wins = sum(1 for t in trades if t.pnl > 0)
    win_rate = wins / len(trades) if trades else 0.0

    returns = [t.pnl for t in trades]
    if len(returns) >= 2:
        mean_ret = sum(returns) / len(returns)
        variance = sum((r - mean_ret) ** 2 for r in returns) / (len(returns) - 1)
        std = variance ** 0.5 if variance > 0 else 0.01
        sharpe = (mean_ret / std) * (252 ** 0.5) if std > 0 else 0.0
    else:
        sharpe = 0.0

    equity = 0.0
    peak = 0.0
    max_dd = 0.0
    for t in trades:
        equity += t.pnl
        peak = max(peak, equity)
        dd = peak - equity
        if dd > max_dd:
            max_dd = dd

    return trades, total_pnl, sharpe, max_dd, win_rate, len(trades)
