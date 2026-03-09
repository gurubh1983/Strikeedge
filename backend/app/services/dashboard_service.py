"""Dashboard service: stocks heatmap, sector heatmap, top winners/losers."""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any

from app.services.fyers_data import get_history, get_quotes

# Nifty 50 stocks (subset for heatmap) - NSE:SYMBOL-EQ
DASHBOARD_STOCKS = [
    "RELIANCE", "TCS", "HDFCBANK", "INFY", "ICICIBANK", "HINDUNILVR", "SBIN",
    "BHARTIARTL", "ITC", "KOTAKBANK", "BAJFINANCE", "LT", "AXISBANK", "ASIANPAINT",
    "MARUTI", "WIPRO", "HCLTECH", "TITAN", "SUNPHARMA", "ULTRACEMCO", "NESTLEIND",
]

# NSE sector/benchmark indices - verify format per Fyers sym_details
DASHBOARD_SECTORS = [
    ("NIFTY50", "Nifty 50"),
    ("NIFTYBANK", "Bank Nifty"),
    ("NIFTYAUTO", "Auto"),
    ("NIFTYIT", "IT"),
    ("NIFTYPHARMA", "Pharma"),
    ("NIFTYFMCG", "FMCG"),
    ("NIFTYMETAL", "Metal"),
    ("NIFTYENERGY", "Energy"),
    ("NIFTYREALTY", "Realty"),
]


def _nse_stock(symbol: str) -> str:
    return f"NSE:{symbol}-EQ"


def _nse_index(symbol: str) -> str:
    return f"NSE:{symbol}-INDEX"


def _last_trading_date() -> str:
    """Return YYYY-MM-DD of most recent market day (exclude Sat/Sun)."""
    d = datetime.now().date()
    while d.weekday() >= 5:  # Sat=5, Sun=6
        d -= timedelta(days=1)
    return d.isoformat()


def _fetch_with_fallback(symbols: list[str]) -> tuple[dict[str, dict], bool]:
    """
    Try live quotes first. If empty/fails, use previous day close from history.
    Returns (symbol -> {ltp, prev_close, change_pct}, used_live)
    """
    quotes = get_quotes(symbols)
    today = datetime.now().date()
    to_d = _last_trading_date()
    from_d = (today - timedelta(days=30)).isoformat()
    out: dict[str, dict[str, Any]] = {}
    used_live = False

    if quotes:
        used_live = True
        for sym, q in quotes.items():
            ltp = q.get("ltp") if isinstance(q.get("ltp"), (int, float)) else None
            prev = q.get("close") or q.get("prev_close_price")
            if prev is None and ltp is not None:
                prev = ltp
            prev_f = float(prev) if prev is not None else None
            ltp_f = float(ltp) if ltp is not None else prev_f
            change_pct = None
            if prev_f and prev_f > 0 and ltp_f is not None:
                change_pct = ((ltp_f - prev_f) / prev_f) * 100
            out[sym] = {
                "ltp": ltp_f,
                "prev_close": prev_f,
                "change_pct": change_pct,
                "symbol": sym,
            }

    # Fallback: previous day close from history (for missing symbols or when quotes has 0% before market open)
    for sym in symbols:
        needs_history = sym not in out
        if not needs_history:
            entry = out[sym]
            # When quotes gave 0% and ltp==prev (e.g. before market open), try history for real day-over-day change
            if entry.get("change_pct") == 0 and entry.get("ltp") == entry.get("prev_close"):
                needs_history = True
                del out[sym]
        if not needs_history:
            continue
        hist = get_history(symbol=sym, resolution="D", from_date=from_d, to_date=to_d)
        if hist and len(hist) >= 2:
            # Use last 2 candles: latest close vs previous close
            last = hist[-1]
            prev_candle = hist[-2]
            close = last.get("c", last.get("close"))
            prev = prev_candle.get("c", prev_candle.get("close"))
            prev_f = float(prev) if prev is not None else None
            close_f = float(close) if close is not None else prev_f
            change_pct = None
            if prev_f and prev_f > 0 and close_f is not None:
                change_pct = ((close_f - prev_f) / prev_f) * 100
            out[sym] = {
                "ltp": close_f,
                "prev_close": prev_f,
                "change_pct": change_pct,
                "symbol": sym,
            }
        elif hist and len(hist) == 1:
            # Only 1 candle: use it as ltp, no change
            last = hist[-1]
            close = last.get("c", last.get("close"))
            close_f = float(close) if close is not None else None
            out[sym] = {"ltp": close_f, "prev_close": close_f, "change_pct": 0.0, "symbol": sym}
    return out, used_live


def _build_heatmap(items: list[tuple[str, str]], to_symbol: callable) -> list[dict]:
    """Build heatmap rows: [{symbol, name, change_pct, ltp}, ...]"""
    symbols = [to_symbol(s[0]) for s in items]
    data, _ = _fetch_with_fallback(symbols)
    rows = []
    for code, name in items:
        sym = to_symbol(code)
        d = data.get(sym, {})
        cp = d.get("change_pct")
        if cp is None:
            cp = 0.0
        rows.append({
            "symbol": code,
            "name": name,
            "change_pct": round(cp, 2),
            "ltp": d.get("ltp"),
        })
    return sorted(rows, key=lambda r: r["change_pct"] or 0, reverse=True)


def _top_n(rows: list[dict], n: int = 5) -> tuple[list[dict], list[dict]]:
    """Return (top winners, top losers) from heatmap rows."""
    sorted_rows = sorted(rows, key=lambda r: r["change_pct"] or 0, reverse=True)
    winners = sorted_rows[:n]
    losers = sorted_rows[-n:][::-1]
    return winners, losers


def get_market_overview() -> dict[str, Any]:
    """Get stocks heatmap, sector heatmap, top 5 winners, top 5 losers."""
    stocks_items = [(s, s) for s in DASHBOARD_STOCKS]
    sectors_items = DASHBOARD_SECTORS

    stock_symbols = [_nse_stock(s) for s in DASHBOARD_STOCKS]
    sector_symbols = [_nse_index(s[0]) for s in DASHBOARD_SECTORS]

    all_symbols = stock_symbols + sector_symbols
    data, used_live = _fetch_with_fallback(all_symbols)

    stocks_heatmap = []
    for s in DASHBOARD_STOCKS:
        sym = _nse_stock(s)
        d = data.get(sym, {})
        cp = d.get("change_pct")
        if cp is None:
            cp = 0.0
        stocks_heatmap.append({"symbol": s, "name": s, "change_pct": round(cp, 2), "ltp": d.get("ltp")})

    sector_heatmap = []
    for code, name in DASHBOARD_SECTORS:
        sym = _nse_index(code)
        d = data.get(sym, {})
        cp = d.get("change_pct")
        if cp is None:
            cp = 0.0
        sector_heatmap.append({"symbol": code, "name": name, "change_pct": round(cp, 2), "ltp": d.get("ltp")})

    all_rows = stocks_heatmap + sector_heatmap
    winners, losers = _top_n(all_rows, 5)

    # Momentum decision metrics
    stock_changes = [r["change_pct"] for r in stocks_heatmap]
    sector_changes = [r["change_pct"] for r in sector_heatmap]
    advance_count = sum(1 for c in stock_changes + sector_changes if c and c > 0)
    decline_count = sum(1 for c in stock_changes + sector_changes if c and c < 0)
    total = advance_count + decline_count
    breadth_pct = round((advance_count / total * 100) if total > 0 else 50, 1)

    avg_stock = round(sum(c or 0 for c in stock_changes) / len(stock_changes), 2) if stock_changes else 0
    avg_sector = round(sum(c or 0 for c in sector_changes) / len(sector_changes), 2) if sector_changes else 0
    strongest = max(sector_heatmap, key=lambda x: x["change_pct"] or 0) if sector_heatmap else None
    weakest = min(sector_heatmap, key=lambda x: x["change_pct"] or 0) if sector_heatmap else None

    # Market context: expansion (>60% up), rotation (40-60%), caution (25-40%), contraction (<25%)
    if breadth_pct >= 60:
        market_context = "expansion"
        context_label = "Expansion"
        context_hint = "Broad strength — consider momentum longs"
    elif breadth_pct >= 40:
        market_context = "rotation"
        context_label = "Rotation"
        context_hint = "Mixed — focus on sector leaders"
    elif breadth_pct >= 25:
        market_context = "caution"
        context_label = "Caution"
        context_hint = "Selective — quality over quantity"
    else:
        market_context = "contraction"
        context_label = "Contraction"
        context_hint = "Defensive — reduce exposure or short"

    return {
        "data_source": "live" if used_live else "previous_close",
        "stocks_heatmap": stocks_heatmap,
        "sector_heatmap": sector_heatmap,
        "top_winners": winners,
        "top_losers": losers,
        "momentum_metrics": {
            "advance_count": advance_count,
            "decline_count": decline_count,
            "breadth_pct": breadth_pct,
            "avg_stock_change": avg_stock,
            "avg_sector_change": avg_sector,
            "strongest_sector": strongest,
            "weakest_sector": weakest,
            "market_context": market_context,
            "context_label": context_label,
            "context_hint": context_hint,
            "nifty50_change": next((r["change_pct"] for r in sector_heatmap if r["symbol"] == "NIFTY50"), 0),
            "bank_nifty_change": next((r["change_pct"] for r in sector_heatmap if r["symbol"] == "NIFTYBANK"), 0),
        },
    }
