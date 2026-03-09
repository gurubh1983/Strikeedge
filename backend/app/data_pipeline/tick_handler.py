from __future__ import annotations

from collections import defaultdict, deque
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone


@dataclass(slots=True)
class Tick:
    token: str
    ltp: float
    volume: int
    ts: datetime


@dataclass(slots=True)
class BuiltCandle:
    token: str
    timeframe: str
    bucket_start: datetime
    open: float
    high: float
    low: float
    close: float
    volume: int


class TickHandler:
    def __init__(self, max_ticks_per_token: int = 1000) -> None:
        self.max_ticks_per_token = max_ticks_per_token
        self.buffer: dict[str, deque[Tick]] = defaultdict(lambda: deque(maxlen=self.max_ticks_per_token))

    def add_tick(self, token: str, ltp: float, volume: int, ts: datetime | None = None) -> None:
        timestamp = ts or datetime.now(timezone.utc)
        self.buffer[token].append(Tick(token=token, ltp=ltp, volume=volume, ts=timestamp))

    def get_ticks(self, token: str) -> list[Tick]:
        return list(self.buffer[token])

    def get_ticks_in_range(self, token: str, start_ts: datetime, end_ts: datetime) -> list[Tick]:
        ticks = self.get_ticks(token)
        return [tick for tick in ticks if start_ts <= tick.ts <= end_ts]

    def build_latest_candle(self, token: str, timeframe: str = "1m") -> BuiltCandle | None:
        ticks = self.get_ticks(token)
        if not ticks:
            return None
        if timeframe not in {"1m", "5m", "15m"}:
            timeframe = "1m"
        bucket_minutes = {"1m": 1, "5m": 5, "15m": 15}[timeframe]
        last_ts = ticks[-1].ts
        bucket_minute = last_ts.minute - (last_ts.minute % bucket_minutes)
        bucket_start = last_ts.replace(second=0, microsecond=0, minute=bucket_minute)
        bucket_end = bucket_start + timedelta(minutes=bucket_minutes)
        in_bucket = [t for t in ticks if bucket_start <= t.ts < bucket_end]
        if not in_bucket:
            return None
        prices = [t.ltp for t in in_bucket]
        return BuiltCandle(
            token=token,
            timeframe=timeframe,
            bucket_start=bucket_start,
            open=in_bucket[0].ltp,
            high=max(prices),
            low=min(prices),
            close=in_bucket[-1].ltp,
            volume=sum(t.volume for t in in_bucket),
        )
