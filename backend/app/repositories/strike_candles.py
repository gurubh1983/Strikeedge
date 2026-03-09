from __future__ import annotations

from datetime import datetime
from uuid import uuid4

from sqlalchemy.orm import Session

from app.db.models import StrikeCandleModel


class StrikeCandleRepository:
    @staticmethod
    def upsert_candle(
        session: Session,
        *,
        symbol: str,
        token: str,
        timeframe: str,
        timestamp: datetime,
        open_price: float,
        high_price: float,
        low_price: float,
        close_price: float,
        volume: int,
    ) -> None:
        existing = (
            session.query(StrikeCandleModel)
            .filter(StrikeCandleModel.symbol == symbol)
            .filter(StrikeCandleModel.timeframe == timeframe)
            .filter(StrikeCandleModel.timestamp == timestamp)
            .first()
        )
        if existing is None:
            session.add(
                StrikeCandleModel(
                    id=str(uuid4()),
                    symbol=symbol,
                    token=token,
                    timeframe=timeframe,
                    timestamp=timestamp,
                    open=open_price,
                    high=high_price,
                    low=low_price,
                    close=close_price,
                    volume=volume,
                )
            )
            return
        existing.token = token
        existing.open = open_price
        existing.high = high_price
        existing.low = low_price
        existing.close = close_price
        existing.volume = volume

    @staticmethod
    def list_candles(
        session: Session,
        *,
        symbol: str,
        timeframe: str,
        limit: int,
    ) -> list[dict]:
        rows = (
            session.query(StrikeCandleModel)
            .filter(StrikeCandleModel.symbol == symbol)
            .filter(StrikeCandleModel.timeframe == timeframe)
            .order_by(StrikeCandleModel.timestamp.desc())
            .limit(limit)
            .all()
        )
        return [
            {
                "timestamp": row.timestamp.isoformat(),
                "open": row.open,
                "high": row.high,
                "low": row.low,
                "close": row.close,
                "volume": row.volume,
            }
            for row in reversed(rows)
        ]
