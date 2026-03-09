from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any

import httpx
import pandas as pd


@dataclass(slots=True)
class HistoricalFetchRequest:
    token: str
    exchange: str
    interval: str
    from_date: str
    to_date: str


class CandleFetcher:
    """
    Fyers API v3 historical fetcher interface.
    Current implementation expects a REST-compatible history endpoint.
    """

    def __init__(self, base_url: str, timeout_seconds: float = 30.0) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout_seconds = timeout_seconds

    async def fetch_historical(self, req: HistoricalFetchRequest) -> list[dict[str, Any]]:
        payload = {
            "symbol": req.token,
            "resolution": req.interval,
            "date_format": "1",
            "range_from": req.from_date,
            "range_to": req.to_date,
            "cont_flag": "1",
        }
        async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
            response = await client.post(f"{self.base_url}/history", json=payload)
            response.raise_for_status()
            data = response.json()
        records = data.get("candles", data.get("data", data if isinstance(data, list) else []))
        out: list[dict[str, Any]] = []
        for row in records:
            if isinstance(row, dict):
                out.append(row)
            elif isinstance(row, list) and len(row) >= 6:
                out.append(
                    {
                        "timestamp": row[0],
                        "open": row[1],
                        "high": row[2],
                        "low": row[3],
                        "close": row[4],
                        "volume": row[5],
                    }
                )
        return out

    @staticmethod
    def to_dataframe(records: list[dict[str, Any]]) -> pd.DataFrame:
        if not records:
            return pd.DataFrame(columns=["timestamp", "open", "high", "low", "close", "volume"])
        frame = pd.DataFrame(records)
        if "timestamp" in frame.columns:
            frame["timestamp"] = pd.to_datetime(frame["timestamp"], errors="coerce")
        return frame

    @staticmethod
    def support_1m(interval: str) -> bool:
        return interval.lower() in {"1m", "one_minute", "1minute", "1min"}
