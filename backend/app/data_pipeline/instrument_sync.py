from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session, sessionmaker

from app.data_pipeline.fyers_client import FyersClient
from app.db.models import InstrumentModel


class InstrumentSyncService:
    def __init__(self, session_factory: sessionmaker[Session], fyers_client: FyersClient | None = None) -> None:
        self.session_factory = session_factory
        self.fyers_client = fyers_client or FyersClient()

    async def sync_nfo_options(
        self,
        *,
        expiry: str | None = None,
        min_strike: float | None = None,
        max_strike: float | None = None,
    ) -> int:
        records = await self.fyers_client.fetch_scrip_master()
        records = self.fyers_client.filter_nfo_options(records)
        if expiry:
            records = self.fyers_client.filter_by_expiry(records, expiry)
        if min_strike is not None and max_strike is not None:
            records = self.fyers_client.filter_by_strike_range(records, min_strike, max_strike)

        normalized = [self.fyers_client.normalize_record(item) for item in records]
        normalized = [item for item in normalized if item["token"]]
        if not normalized:
            return 0

        upserted = 0
        with self.session_factory() as session:
            for item in normalized:
                existing = session.get(InstrumentModel, item["token"])
                if existing is None:
                    session.add(InstrumentModel(**item))
                    upserted += 1
                else:
                    for key, value in item.items():
                        setattr(existing, key, value)
                    upserted += 1
            session.commit()
        return upserted
