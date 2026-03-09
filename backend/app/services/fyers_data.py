"""Fyers REST API data service: quotes, option chain, historical candles."""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any

from app.services.fyers_token_store import load_token


def _get_fyers_model():
    """Create FyersModel with stored token. Returns None if no token."""
    token = load_token()
    if not token:
        return None
    from app.core.settings import get_settings
    settings = get_settings()
    app_id = settings.fyers_app_id_resolved
    if not app_id:
        return None
    from fyers_apiv3 import fyersModel
    return fyersModel.FyersModel(client_id=app_id, token=token, is_async=False)


def get_quotes(symbols: list[str]) -> dict[str, dict[str, Any]]:
    """
    Fetch live quotes for symbols.
    Symbols: NSE:NIFTY50-INDEX, NSE:BANKNIFTY-INDEX, NSE:NIFTY24APR24000CE, etc.
    Returns dict of symbol -> {ltp, high, low, open, close, volume, ...}
    """
    fm = _get_fyers_model()
    if fm is None:
        return {}
    try:
        data = {"symbols": ",".join(symbols)}
        resp = fm.quotes(data=data)
        if not isinstance(resp, dict):
            return {}
        d = resp.get("d", resp.get("data", []))
        if not d:
            return {}
        out: dict[str, dict[str, Any]] = {}
        for item in (d if isinstance(d, list) else [d]):
            sym = str(item.get("n", item.get("symbol", ""))).strip()
            v = item.get("v", {})
            if isinstance(v, dict):
                ltp = v.get("lp")
                open_price = v.get("open_price")
                high_price = v.get("high_price")
                low_price = v.get("low_price")
                close_price = v.get("prev_close_price", ltp)
                volume = v.get("volume", 0)
            else:
                ltp = item.get("lp", item.get("ltp"))
                open_price = item.get("o", item.get("open"))
                high_price = item.get("h", item.get("high"))
                low_price = item.get("l", item.get("low"))
                close_price = item.get("c", item.get("close", ltp))
                volume = v if isinstance(v, (int, float)) else 0
            if sym:
                out[sym] = {
                    "symbol": sym,
                    "ltp": ltp,
                    "open": open_price,
                    "high": high_price,
                    "low": low_price,
                    "close": close_price,
                    "volume": volume,
                }
        return out
    except Exception as e:
        print(f"[fyers_data] get_quotes error: {e}")
        return {}


def get_spot_price(underlying: str) -> float | None:
    """Get live spot/index price for NIFTY or BANKNIFTY."""
    symbol_map = {
        "NIFTY": "NSE:NIFTY50-INDEX",
        "BANKNIFTY": "NSE:NIFTYBANK-INDEX",
        "NIFTY50": "NSE:NIFTY50-INDEX",
        "NIFTYBANK": "NSE:NIFTYBANK-INDEX",
    }
    sym = symbol_map.get(underlying.upper(), f"NSE:{underlying.upper()}-INDEX")
    quotes = get_quotes([sym])
    if sym in quotes:
        ltp = quotes[sym].get("ltp")
        return float(ltp) if ltp is not None else None
    return None


def _fallback_expiries(count: int = 8) -> list[dict[str, Any]]:
    """Generate fallback expiry dates (Thursdays) when Fyers is unavailable."""
    out = []
    today = datetime.now().date()
    # Find next Thursday
    days_ahead = (3 - today.weekday() + 7) % 7  # Thu=3
    if days_ahead == 0:
        days_ahead = 7
    d = today + timedelta(days=days_ahead)
    for _ in range(count):
        out.append({
            "date": d.strftime("%d-%m-%Y"),
            "iso": d.strftime("%Y-%m-%d"),
            "expiry": int(datetime.combine(d, datetime.min.time()).timestamp()),
        })
        d += timedelta(days=7)
    return out


def get_expiries(underlying: str) -> list[dict[str, Any]]:
    """Return list of available expiry dates for an underlying. Format: [{"date": "DD-MM-YYYY", "expiry": ts}, ...]"""
    fm = _get_fyers_model()
    symbol_map = {
        "NIFTY": "NSE:NIFTY50-INDEX",
        "BANKNIFTY": "NSE:NIFTYBANK-INDEX",
        "FINNIFTY": "NSE:FINNIFTY-INDEX",
    }
    sym = symbol_map.get(underlying.upper(), f"NSE:{underlying.upper()}-INDEX")
    if fm is not None:
        try:
            resp = fm.optionchain(data={"symbol": sym, "strikecount": 1})
            if resp.get("s") == "ok":
                expiry_data = resp.get("data", {}).get("expiryData", [])
                if expiry_data:
                    out = []
                    for ed in expiry_data:
                        date_str = ed.get("date")
                        ts = ed.get("expiry")
                        if date_str:
                            try:
                                dt = datetime.strptime(date_str, "%d-%m-%Y")
                                iso = dt.strftime("%Y-%m-%d")
                                out.append({"date": date_str, "iso": iso, "expiry": ts})
                            except ValueError:
                                out.append({"date": date_str, "iso": "", "expiry": ts})
                    return out
        except Exception:
            pass
    return _fallback_expiries()


def _expiry_to_timestamp(expiry: str) -> int:
    """Convert YYYY-MM-DD to epoch seconds for Fyers API."""
    try:
        dt = datetime.strptime(expiry.strip()[:10], "%Y-%m-%d")
        return int(dt.timestamp())
    except ValueError:
        return 0


def get_option_chain(underlying: str, expiry: str, strikecount: int = 15) -> list[dict[str, Any]]:
    """
    Fetch options chain with OI, LTP from Fyers API.
    underlying: NIFTY, BANKNIFTY
    expiry: 2026-03-10 (YYYY-MM-DD) or will use nearest expiry if invalid
    """
    fm = _get_fyers_model()
    if fm is None:
        return []
    symbol_map = {
        "NIFTY": "NSE:NIFTY50-INDEX",
        "BANKNIFTY": "NSE:NIFTYBANK-INDEX",
        "FINNIFTY": "NSE:FINNIFTY-INDEX",
    }
    sym = symbol_map.get(underlying.upper(), f"NSE:{underlying.upper()}-INDEX")
    
    try:
        # First get valid expiries
        resp = fm.optionchain(data={"symbol": sym, "strikecount": 1})
        if resp.get("s") != "ok":
            return []
        
        expiry_data = resp.get("data", {}).get("expiryData", [])
        if not expiry_data:
            return []
        
        # Find matching expiry or use nearest
        target_ts = None
        if expiry:
            # Try to match the provided expiry date
            try:
                exp_date = datetime.strptime(expiry.strip()[:10], "%Y-%m-%d")
                exp_str = exp_date.strftime("%d-%m-%Y")
                for ed in expiry_data:
                    if ed.get("date") == exp_str:
                        target_ts = int(ed.get("expiry", 0))
                        break
            except ValueError:
                pass
        
        # Use nearest expiry if no match found
        if not target_ts and expiry_data:
            target_ts = int(expiry_data[0].get("expiry", 0))
        
        if not target_ts:
            return []
        
        # Now fetch option chain with valid expiry
        data = {"symbol": sym, "timestamp": target_ts, "strikecount": strikecount}
        resp = fm.optionchain(data=data)
        if resp.get("s") != "ok":
            return []
        
        chain = resp.get("data", {}).get("optionsChain", [])
        out: list[dict[str, Any]] = []
        
        for row in chain:
            if not isinstance(row, dict):
                continue
            strike = row.get("strike_price")
            opt_type = row.get("option_type", "")
            if strike is None or strike < 0 or not opt_type:
                continue  # Skip the underlying index entry
            
            out.append({
                "strike_price": float(strike),
                "option_type": opt_type,
                "symbol": row.get("symbol", ""),
                "token": row.get("fyToken", row.get("symbol", "")),
                "oi": row.get("oi", 0),
                "oi_change": row.get("oich", 0),
                "ltp": row.get("ltp"),
                "ltp_change": row.get("ltpch", 0),
                "volume": row.get("volume", 0),
                "bid": row.get("bid"),
                "ask": row.get("ask"),
            })
        
        return sorted(out, key=lambda x: (x["strike_price"], x["option_type"]))
    except Exception as e:
        print(f"[fyers_data] get_option_chain error: {e}")
        return []


def get_candles_for_symbol(
    symbol: str,
    timeframe: str = "5m",
    limit: int = 200,
) -> list[dict[str, Any]] | None:
    """
    Fetch candles from Fyers for a strike symbol.
    Returns list of candles or None if Fyers unavailable.
    Used by chart/candles APIs to serve live Fyers data.
    """
    sym = symbol.strip()
    if ":" not in sym and sym:
        sym = f"NSE:{sym}"
    if not load_token() or not sym:
        return None
    res_map = {
        "1m": "1", "2m": "2", "3m": "3", "5m": "5", "10m": "10", "15m": "15",
        "20m": "20", "30m": "30", "45m": "45", "1h": "60", "2h": "120",
        "3h": "180", "4h": "240", "1d": "D", "1w": "D",
    }
    res = res_map.get((timeframe or "5m").lower(), "5")
    today = datetime.now().date()
    to_d = today.isoformat()
    from_d = (today - timedelta(days=30)).isoformat()
    candles = get_history(symbol=sym, resolution=res, from_date=from_d, to_date=to_d)
    if not candles:
        return None
    out = []
    for row in candles:
        ts = row.get("timestamp")
        if isinstance(ts, (int, float)):
            from datetime import datetime as dt, timezone
            ts = dt.fromtimestamp(ts, tz=timezone.utc).isoformat()
        elif ts and not isinstance(ts, str):
            ts = str(ts)
        out.append({
            "timestamp": ts or row.get("timestamp"),
            "open": float(row.get("open", 0)),
            "high": float(row.get("high", 0)),
            "low": float(row.get("low", 0)),
            "close": float(row.get("close", 0)),
            "volume": int(row.get("volume", 0)),
        })
    return out[-limit:] if len(out) > limit else out


def get_history(
    symbol: str,
    resolution: str = "5",
    from_date: str = "",
    to_date: str = "",
) -> list[dict[str, Any]]:
    """
    Fetch historical candles.
    symbol: NSE:NIFTY24APR24000CE, etc.
    resolution: 1 (1m), 5 (5m), 60 (1h), D (1d)
    from_date, to_date: YYYY-MM-DD
    """
    fm = _get_fyers_model()
    if fm is None:
        return []
    if not from_date or not to_date:
        today = datetime.now().date()
        to_date = today.isoformat()
        from_date = (today - timedelta(days=30)).isoformat()
    try:
        data = {
            "symbol": symbol,
            "resolution": resolution,
            "date_format": 1,
            "range_from": from_date,
            "range_to": to_date,
        }
        resp = fm.history(data=data)
        if not isinstance(resp, dict):
            return []
        candles = resp.get("candles", resp.get("data", resp.get("d", [])))
        if not isinstance(candles, list):
            return []
        out: list[dict[str, Any]] = []
        for row in candles:
            if isinstance(row, list) and len(row) >= 6:
                out.append({
                    "timestamp": row[0],
                    "open": row[1],
                    "high": row[2],
                    "low": row[3],
                    "close": row[4],
                    "volume": row[5] if len(row) > 5 else 0,
                })
            elif isinstance(row, dict):
                out.append(row)
        return out
    except Exception as e:
        print(f"[fyers_data] get_history error for {symbol}: {e}")
        return []