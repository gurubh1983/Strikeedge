from __future__ import annotations

from pathlib import Path

from app.core.file_cache import FileCache
from app.data_pipeline.fyers_client import FyersClient


def test_filter_nfo_options() -> None:
    records = [
        {"exch_seg": "NFO", "instrumenttype": "OPTIDX", "symbol": "NIFTY24APR24000CE"},
        {"exch_seg": "NFO", "instrumenttype": "FUTIDX", "symbol": "NIFTY24APRFUT"},
        {"exch_seg": "NSE", "instrumenttype": "OPTIDX", "symbol": "NIFTY24APR24000PE"},
        {"exch_seg": "NFO", "instrumenttype": "OPTIDX", "symbol": "NIFTY24APR24000PE"},
    ]
    out = FyersClient.filter_nfo_options(records)
    assert len(out) == 2


def test_filter_by_expiry_and_strike_range() -> None:
    records = [
        {"expiry": "2026-04-24", "strike": "2400000"},
        {"expiry": "2026-04-24", "strike": "2500000"},
        {"expiry": "2026-05-01", "strike": "2400000"},
    ]
    by_expiry = FyersClient.filter_by_expiry(records, "2026-04-24")
    assert len(by_expiry) == 2
    by_strike = FyersClient.filter_by_strike_range(by_expiry, 23900, 24500)
    assert len(by_strike) == 1


def test_file_cache_set_get(tmp_path: Path) -> None:
    cache = FileCache(cache_dir=str(tmp_path / "cache"))
    cache.set("k1", {"v": 1}, ttl_seconds=60)
    assert cache.get("k1") == {"v": 1}


def test_build_options_chain_from_scrip_master_records() -> None:
    records = [
        {
            "exch_seg": "NFO",
            "instrumenttype": "OPTIDX",
            "symbol": "NIFTY24APR24000CE",
            "name": "NIFTY",
            "expiry": "2026-04-24",
            "strike": "2400000",
            "token": "111",
            "lotsize": 50,
            "oi": "12000",
            "iv": "16.5",
        },
        {
            "exch_seg": "NFO",
            "instrumenttype": "OPTIDX",
            "symbol": "NIFTY24APR24000PE",
            "name": "NIFTY",
            "expiry": "2026-04-24",
            "strike": "2400000",
            "token": "112",
            "lotsize": 50,
            "oi": "13000",
            "iv": "17.1",
        },
    ]
    rows = FyersClient.build_options_chain(records, underlying="NIFTY", expiry="2026-04-24")
    assert len(rows) == 1
    assert rows[0]["strike_price"] == 24000
    assert rows[0]["call_token"] == "111"
    assert rows[0]["put_token"] == "112"
    assert rows[0]["call_oi"] == 12000
    assert rows[0]["put_oi"] == 13000
    assert rows[0]["put_call_ratio"] is not None
