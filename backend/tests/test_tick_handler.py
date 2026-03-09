from __future__ import annotations

from datetime import datetime, timezone

from app.data_pipeline.tick_handler import TickHandler


def test_tick_buffer_limit() -> None:
    handler = TickHandler(max_ticks_per_token=3)
    now = datetime.now(timezone.utc)
    handler.add_tick("T1", 100, 10, now)
    handler.add_tick("T1", 101, 20, now)
    handler.add_tick("T1", 102, 30, now)
    handler.add_tick("T1", 103, 40, now)
    ticks = handler.get_ticks("T1")
    assert len(ticks) == 3
    assert ticks[-1].ltp == 103


def test_build_latest_candle() -> None:
    handler = TickHandler(max_ticks_per_token=10)
    base = datetime(2026, 3, 8, 9, 15, 10, tzinfo=timezone.utc)
    handler.add_tick("T2", 100, 10, base)
    handler.add_tick("T2", 101, 20, base.replace(second=20))
    handler.add_tick("T2", 99, 30, base.replace(second=45))

    candle = handler.build_latest_candle("T2", timeframe="1m")
    assert candle is not None
    assert candle.open == 100
    assert candle.close == 99
    assert candle.high == 101
    assert candle.low == 99
    assert candle.volume == 60


def test_get_ticks_in_range() -> None:
    handler = TickHandler(max_ticks_per_token=10)
    t1 = datetime(2026, 3, 8, 9, 15, 0, tzinfo=timezone.utc)
    t2 = datetime(2026, 3, 8, 9, 16, 0, tzinfo=timezone.utc)
    t3 = datetime(2026, 3, 8, 9, 17, 0, tzinfo=timezone.utc)
    handler.add_tick("T3", 100, 1, t1)
    handler.add_tick("T3", 101, 1, t2)
    handler.add_tick("T3", 102, 1, t3)

    out = handler.get_ticks_in_range("T3", t1, t2)
    assert len(out) == 2
