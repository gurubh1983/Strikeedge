"""Technical scanner: strike-level RSI, MACD, EMA on option strike charts."""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any

import pandas as pd

from app.domain.indicators import ema, macd, rsi
from app.services.fyers_data import get_expiries, get_history, get_option_chain
from app.services.fyers_token_store import load_token
from app.services.market_data import market_data_service


def _ensure_fyers_symbol(sym: str) -> str:
    """Ensure symbol has NSE: prefix for Fyers API."""
    s = (sym or "").strip()
    if not s:
        return ""
    if ":" in s:
        return s
    return f"NSE:{s}"


# Fyers API: resolutions 1,2,3,5,10,15,20,30,45,60,120,180,240 min; D for daily
# Up to 100 days per request for minute resolutions
FYERS_RESOLUTION_MAP = {
    "1m": "1", "2m": "2", "3m": "3", "5m": "5", "10m": "10", "15m": "15",
    "20m": "20", "30m": "30", "45m": "45", "1h": "60", "2h": "120",
    "3h": "180", "4h": "240", "1d": "D", "1w": "D",
}


def _timeframe_to_resolution(tf: str) -> str:
    """Convert timeframe to Fyers resolution per API docs."""
    return FYERS_RESOLUTION_MAP.get((tf or "").strip().lower(), "5")


def _candles_per_day(timeframe: str) -> float:
    """Approximate candles per trading day (9:15–15:30 = 375 min)."""
    tf = (timeframe or "5m").lower()
    if tf == "1d" or tf == "1w":
        return 1.0
    try:
        n = int(tf.replace("m", "").replace("h", ""))
        if "h" in tf:
            return 375 / (n * 60)
        return 375 / n
    except ValueError:
        return 75.0


def _min_candles_from_filter_config(config: dict | None) -> int:
    """Extract min required candles from filter conditions (max indicator period)."""
    if not config:
        return 35
    best = 35
    for g in config.get("groups", []):
        for c in g.get("conditions", []):
            for side in ("left", "right"):
                v = c.get(side)
                if not isinstance(v, dict) or v.get("type") != "indicator":
                    continue
                params = v.get("params") or {}
                period = params.get("period")
                rsi_p = params.get("rsi") or params.get("rsi_period")
                sma_p = params.get("sma") or params.get("sma_period")
                k_p = params.get("k") or params.get("k_period")
                n_p = params.get("n")
                if period is not None:
                    best = max(best, int(period) + 10)
                if rsi_p is not None:
                    best = max(best, int(rsi_p) + 10)
                if sma_p is not None:
                    best = max(best, int(sma_p) + 10)
                if k_p is not None:
                    best = max(best, int(k_p) + 10)
                if n_p is not None:
                    best = max(best, int(n_p) + 10)
            for p in (c.get("left") or {}).get("params") or {}, (c.get("right") or {}).get("params") or {}:
                for val in p.values():
                    if isinstance(val, (int, float)) and val > best:
                        best = max(best, int(val) + 10)
    return best


def _required_candle_days(timeframe: str, filter_config: dict | None, max_days: int = 100) -> int:
    """Compute candle_days needed. Fyers allows up to 100 days for minute resolutions."""
    import math
    min_c = _min_candles_from_filter_config(filter_config)
    cpd = _candles_per_day(timeframe)
    if cpd <= 0:
        return max_days
    days = math.ceil(min_c / cpd) + 1
    return min(max(5, days), max_days)


def compute_indicators(candles: list[dict[str, Any]]) -> dict[str, float | None]:
    """Compute RSI(14), EMA(20), MACD from OHLCV candles. Returns latest values."""
    if not candles or len(candles) < 27:
        return {"rsi_14": None, "ema_20": None, "macd": None, "macd_signal": None}
    closes = []
    for c in candles:
        v = c.get("close") if isinstance(c, dict) else (c[4] if isinstance(c, (list, tuple)) and len(c) > 4 else None)
        if v is not None:
            closes.append(float(v))
    if len(closes) < 27:
        return {"rsi_14": None, "ema_20": None, "macd": None, "macd_signal": None}
    rsi_val = rsi(closes, period=14)
    ema_val = ema(closes, period=20)
    macd_val, macd_sig = macd(closes)
    return {
        "rsi_14": rsi_val,
        "ema_20": ema_val,
        "macd": macd_val,
        "macd_signal": macd_sig,
    }


def _evaluate_rule(value: float | None, operator: str, target: float) -> bool:
    if value is None:
        return False
    v = float(value)
    op = (operator or "").strip().lower()
    if op in (">", "gt"):
        return v > target
    if op in ("<", "lt"):
        return v < target
    if op in (">=", "gte"):
        return v >= target
    if op in ("<=", "lte"):
        return v <= target
    if op in ("==", "=", "eq"):
        return abs(v - target) < 1e-6
    return False


def _get_candles_for_symbol(symbol: str, timeframe: str, days: int) -> list[dict[str, Any]]:
    """Fetch candles from Fyers or fallback to DB."""
    sym = _ensure_fyers_symbol(symbol)
    if load_token() and sym:
        today = datetime.now().date()
        to_d = today.isoformat()
        from_d = (today - timedelta(days=days)).isoformat()
        res = _timeframe_to_resolution(timeframe)
        candles = get_history(symbol=sym, resolution=res, from_date=from_d, to_date=to_d)
        if candles:
            return candles
    rows = market_data_service.get_strike_candles(symbol=symbol, timeframe=timeframe, limit=200)
    if rows:
        return [
            {
                "timestamp": r.get("timestamp"),
                "open": r.get("open"),
                "high": r.get("high"),
                "low": r.get("low"),
                "close": r.get("close"),
                "volume": r.get("volume", 0),
            }
            for r in rows
        ]
    return []


def _candles_to_df(candles: list[dict[str, Any]]) -> pd.DataFrame:
    """Convert candle list to OHLCV DataFrame for FilterEngine."""
    if not candles:
        return pd.DataFrame(columns=["open", "high", "low", "close", "volume"])
    df = pd.DataFrame(candles)
    col_map = {"o": "open", "h": "high", "l": "low", "c": "close", "v": "volume"}
    df = df.rename(columns={k: v for k, v in col_map.items() if k in df.columns})
    return df.reindex(columns=["open", "high", "low", "close", "volume"], fill_value=0)


F_O_UNDERLYINGS = ["NIFTY", "BANKNIFTY", "FINNIFTY"]


def scan_strikes(
    underlyings: list[str] | None,
    expiry: str | None,
    rules: list[dict[str, Any]],
    timeframe: str = "5m",
    candle_days: int = 5,
    max_strikes_per_underlying: int = 30,
    filter_config: dict | None = None,
) -> list[dict[str, Any]]:
    """
    Scan option strikes by technical indicators on strike price charts.
    rules: [{"indicator": "rsi_14", "operator": ">", "value": 60}, ...]
    filter_config: Advanced filter with groups/conditions (synced with ScreenerBuilder).
    underlyings=None: scan all F&O (NIFTY, BANKNIFTY, FINNIFTY).
    expiry=None: scan all expiries for each underlying.
    """
    eff_underlyings = underlyings or F_O_UNDERLYINGS
    if filter_config and filter_config.get("groups"):
        eff_days = _required_candle_days(timeframe, filter_config)
        return _scan_strikes_filter_engine(
            eff_underlyings, expiry, timeframe, eff_days, max_strikes_per_underlying, filter_config
        )
    results: list[dict[str, Any]] = []
    for underlying in eff_underlyings:
        chain = get_option_chain(underlying.upper(), expiry or "", strikecount=max_strikes_per_underlying)
        if not chain:
            continue
        for row in chain:
            symbol = row.get("symbol") or row.get("token")
            if not symbol:
                continue
            candles = _get_candles_for_symbol(symbol, timeframe, candle_days)
            if len(candles) < 20:
                continue
            indicators = compute_indicators(candles)
            matched = True
            for rule in rules:
                ind = (rule.get("indicator") or "").strip().lower().replace(" ", "_")
                if ind == "rsi14":
                    ind = "rsi_14"
                elif ind == "ema20":
                    ind = "ema_20"
                val = indicators.get(ind)
                target = float(rule.get("value", 0))
                op = str(rule.get("operator", ">"))
                if not _evaluate_rule(val, op, target):
                    matched = False
                    break
            if matched:
                results.append({
                    "symbol": symbol,
                    "underlying": underlying.upper(),
                    "strike_price": row.get("strike_price"),
                    "option_type": row.get("option_type"),
                    "ltp": row.get("ltp"),
                    "oi": row.get("oi"),
                    "expiry": expiry or None,
                    "indicators": {k: round(v, 4) if v is not None and isinstance(v, (int, float)) else v for k, v in indicators.items()},
                })
    return results


def _scan_strikes_filter_engine(
    underlyings: list[str],
    expiry: str | None,
    timeframe: str,
    candle_days: int,
    max_strikes_per_underlying: int,
    filter_config: dict,
) -> list[dict[str, Any]]:
    """Scan using FilterEngine. Only includes strikes with enough history to evaluate the condition."""
    from app.services.filter_engine import FilterEngine
    engine = FilterEngine()
    min_candles = _min_candles_from_filter_config(filter_config)
    results: list[dict[str, Any]] = []
    for underlying in underlyings:
        expiries_to_scan: list[str] = []
        if expiry:
            expiries_to_scan = [expiry]
        else:
            for ed in get_expiries(underlying):
                iso_d = ed.get("iso")
                if iso_d and len(iso_d) >= 10:
                    expiries_to_scan.append(iso_d[:10])
                elif ed.get("date"):
                    try:
                        d = datetime.strptime(ed["date"], "%d-%m-%Y")
                        expiries_to_scan.append(d.strftime("%Y-%m-%d"))
                    except ValueError:
                        pass
            if not expiries_to_scan:
                expiries_to_scan = [""]
        for exp in expiries_to_scan:
            chain = get_option_chain(underlying.upper(), exp, strikecount=max_strikes_per_underlying)
            if not chain:
                continue
            for row in chain:
                symbol = row.get("symbol") or row.get("token")
                if not symbol:
                    continue
                candles = _get_candles_for_symbol(symbol, timeframe, candle_days)
                if len(candles) < min_candles:
                    continue
                df = _candles_to_df(candles)
                if df.empty or len(df) < 5:
                    continue
                options_data = {
                    "delta": row.get("delta"),
                    "gamma": row.get("gamma"),
                    "theta": row.get("theta"),
                    "vega": row.get("vega"),
                    "iv": row.get("iv"),
                    "oi": row.get("oi"),
                    "oi_change": row.get("oi_change"),
                }
                try:
                    if engine.evaluate_filter_config(df, filter_config, options_data):
                        indicators = compute_indicators(candles)
                        results.append({
                            "symbol": symbol,
                            "underlying": underlying.upper(),
                            "strike_price": row.get("strike_price"),
                            "option_type": row.get("option_type"),
                            "ltp": row.get("ltp"),
                            "oi": row.get("oi"),
                            "expiry": exp if exp else None,
                            "indicators": {k: round(v, 4) if v is not None and isinstance(v, (int, float)) else v for k, v in indicators.items()},
                        })
                except Exception:
                    pass
    return results
