from __future__ import annotations

import asyncio

from app.core.settings import get_settings
from app.data_pipeline.instrument_sync import InstrumentSyncService
from app.db.session import get_session_factory, init_db


async def main() -> None:
    settings = get_settings()
    init_db(settings)
    session_factory = get_session_factory(settings)
    sync_service = InstrumentSyncService(session_factory)
    count = await sync_service.sync_nfo_options()
    print(f"Synced {count} NFO option instruments.")


if __name__ == "__main__":
    asyncio.run(main())
