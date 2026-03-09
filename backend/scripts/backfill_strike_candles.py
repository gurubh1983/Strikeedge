from __future__ import annotations

import argparse
import asyncio
from datetime import datetime

from app.core.settings import get_settings
from app.data_pipeline.candle_fetcher import CandleFetcher, HistoricalFetchRequest
from app.db.session import get_session_factory, init_db
from app.repositories.strike_candles import StrikeCandleRepository
from app.services.instruments import instrument_query_service


def _parse_iso(dt: str) -> datetime:
    return datetime.fromisoformat(dt.replace("Z", "+00:00"))


async def backfill(symbol: str, timeframe: str, from_date: str, to_date: str, exchange: str = "NFO") -> int:
    settings = get_settings()
    init_db(settings)
    session_factory = get_session_factory(settings)
    instrument_query_service.set_session_factory(session_factory)
    token = instrument_query_service.resolve_token(symbol)
    fetcher = CandleFetcher(base_url=settings.fyers_rest_base_url)
    rows = await fetcher.fetch_historical(
        HistoricalFetchRequest(
            token=token,
            exchange=exchange,
            interval=timeframe,
            from_date=from_date,
            to_date=to_date,
        )
    )
    inserted = 0
    with session_factory() as session:
        for row in rows:
            ts = row.get("timestamp")
            if not isinstance(ts, str):
                continue
            StrikeCandleRepository.upsert_candle(
                session,
                symbol=symbol,
                token=token,
                timeframe=timeframe,
                timestamp=_parse_iso(ts),
                open_price=float(row.get("open", 0.0)),
                high_price=float(row.get("high", 0.0)),
                low_price=float(row.get("low", 0.0)),
                close_price=float(row.get("close", 0.0)),
                volume=int(row.get("volume", 0)),
            )
            inserted += 1
        session.commit()
    return inserted


def main() -> None:
    parser = argparse.ArgumentParser(description="Backfill strike candles for a symbol")
    parser.add_argument("--symbol", required=True)
    parser.add_argument("--timeframe", default="ONE_MINUTE")
    parser.add_argument("--from-date", required=True)
    parser.add_argument("--to-date", required=True)
    parser.add_argument("--exchange", default="NFO")
    args = parser.parse_args()
    inserted = asyncio.run(backfill(args.symbol, args.timeframe, args.from_date, args.to_date, exchange=args.exchange))
    print(f"Inserted/updated {inserted} candles for {args.symbol}")


if __name__ == "__main__":
    main()
