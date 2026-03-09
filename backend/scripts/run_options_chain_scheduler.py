from __future__ import annotations

import argparse
import asyncio

from app.core.settings import get_settings
from app.db.session import get_session_factory, init_db
from app.services.options_chain import options_chain_service


async def main() -> None:
    parser = argparse.ArgumentParser(description="Periodic options chain refresh runner")
    parser.add_argument("--underlying", default="NIFTY")
    parser.add_argument("--expiry", required=True)
    parser.add_argument("--interval-seconds", type=int, default=300)
    args = parser.parse_args()

    settings = get_settings()
    init_db(settings)
    options_chain_service.set_session_factory(get_session_factory(settings))

    while True:
        count = await options_chain_service.refresh_chain(underlying=args.underlying, expiry=args.expiry)
        print({"refreshed_rows": count, "underlying": args.underlying, "expiry": args.expiry})
        await asyncio.sleep(args.interval_seconds)


if __name__ == "__main__":
    asyncio.run(main())
