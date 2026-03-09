from __future__ import annotations

import asyncio
from datetime import datetime, timezone

from app.core.settings import get_settings
from app.db.models import InstrumentModel
from app.db.session import get_session_factory, init_db
from app.services.market_data import market_data_service


async def main() -> None:
    settings = get_settings()
    init_db(settings)
    session_factory = get_session_factory(settings)
    market_data_service.set_session_factory(session_factory)

    while True:
        with session_factory() as session:
            rows = session.query(InstrumentModel).limit(25).all()
        now = datetime.now(timezone.utc)
        for row in rows:
            market_data_service.ingest_tick(
                token=row.token,
                ltp=100.0,
                volume=1,
                timeframe="1m",
                ts=now,
            )
        await asyncio.sleep(60)


if __name__ == "__main__":
    asyncio.run(main())
