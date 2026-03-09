from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from sqlalchemy.orm import Session, sessionmaker

from app.data_pipeline.tick_handler import TickHandler
from app.db.models import CandleModel, IndicatorValueModel
from app.domain.indicators import ema, macd, rsi
from app.repositories.strike_candles import StrikeCandleRepository
from app.services.instruments import instrument_query_service
from app.services.signals import signal_detector


class MarketDataService:
    def __init__(self) -> None:
        self._session_factory: sessionmaker[Session] | None = None
        self.tick_handler = TickHandler(max_ticks_per_token=5000)

    def set_session_factory(self, session_factory: sessionmaker[Session]) -> None:
        self._session_factory = session_factory

    def ingest_tick(
        self,
        *,
        token: str,
        ltp: float,
        volume: int,
        timeframe: str = "1m",
        ts: datetime | None = None,
    ) -> dict[str, Any]:
        timestamp = ts or datetime.now(timezone.utc)
        self.tick_handler.add_tick(token=token, ltp=ltp, volume=volume, ts=timestamp)
        candle = self.tick_handler.build_latest_candle(token=token, timeframe=timeframe)
        if candle is None:
            return {"ingested": True, "candle_persisted": False}
        if self._session_factory is None:
            return {"ingested": True, "candle_persisted": False}

        with self._session_factory() as session:
            existing = (
                session.query(CandleModel)
                .filter(CandleModel.token == token)
                .filter(CandleModel.timeframe == timeframe)
                .filter(CandleModel.timestamp == candle.bucket_start)
                .first()
            )
            if existing is None:
                session.add(
                    CandleModel(
                        id=str(uuid4()),
                        token=token,
                        timeframe=timeframe,
                        timestamp=candle.bucket_start,
                        open=candle.open,
                        high=candle.high,
                        low=candle.low,
                        close=candle.close,
                        volume=candle.volume,
                    )
                )
            else:
                existing.open = candle.open
                existing.high = candle.high
                existing.low = candle.low
                existing.close = candle.close
                existing.volume = candle.volume

            strike_symbol = token
            instrument_token = instrument_query_service.resolve_token(token)
            StrikeCandleRepository.upsert_candle(
                session,
                symbol=strike_symbol,
                token=instrument_token,
                timeframe=timeframe,
                timestamp=candle.bucket_start,
                open_price=candle.open,
                high_price=candle.high,
                low_price=candle.low,
                close_price=candle.close,
                volume=candle.volume,
            )

            session.commit()
            self._refresh_indicator_snapshot(session, token=token, timeframe=timeframe)
            latest_row, previous_row = self._latest_and_previous_for_token(session, token=token, timeframe=timeframe)
            if latest_row is not None:
                events = signal_detector.detect_crossovers(token, timeframe, previous_row, latest_row)
                signal_detector.save_events(events, session=session)
            session.commit()
        return {"ingested": True, "candle_persisted": True}

    def _refresh_indicator_snapshot(self, session: Session, *, token: str, timeframe: str) -> None:
        candles = (
            session.query(CandleModel)
            .filter(CandleModel.token == token)
            .filter(CandleModel.timeframe == timeframe)
            .order_by(CandleModel.timestamp.asc())
            .limit(120)
            .all()
        )
        if len(candles) < 15:
            return
        closes = [float(c.close) for c in candles]
        rsi_14 = rsi(closes, period=14)
        ema_20 = ema(closes, period=20)
        macd_value, macd_signal = macd(closes)
        latest_ts = candles[-1].timestamp

        existing = (
            session.query(IndicatorValueModel)
            .filter(IndicatorValueModel.token == token)
            .filter(IndicatorValueModel.timeframe == timeframe)
            .filter(IndicatorValueModel.timestamp == latest_ts)
            .first()
        )
        if existing is None:
            session.add(
                IndicatorValueModel(
                    id=str(uuid4()),
                    token=token,
                    timeframe=timeframe,
                    timestamp=latest_ts,
                    rsi_14=rsi_14,
                    ema_20=ema_20,
                    macd=macd_value,
                    macd_signal=macd_signal,
                )
            )
        else:
            existing.rsi_14 = rsi_14
            existing.ema_20 = ema_20
            existing.macd = macd_value
            existing.macd_signal = macd_signal

    def get_chart(self, *, token: str, timeframe: str = "5m", limit: int = 100) -> list[dict[str, Any]]:
        if self._session_factory is None:
            return []
        with self._session_factory() as session:
            rows = (
                session.query(CandleModel)
                .filter(CandleModel.token == token)
                .filter(CandleModel.timeframe == timeframe)
                .order_by(CandleModel.timestamp.desc())
                .limit(limit)
                .all()
            )
            out = []
            for row in reversed(rows):
                out.append(
                    {
                        "timestamp": row.timestamp.isoformat(),
                        "open": row.open,
                        "high": row.high,
                        "low": row.low,
                        "close": row.close,
                        "volume": row.volume,
                    }
                )
            return out

    def get_strike_candles(self, *, symbol: str, timeframe: str = "1m", limit: int = 200) -> list[dict[str, Any]]:
        if self._session_factory is None:
            return []
        with self._session_factory() as session:
            return StrikeCandleRepository.list_candles(session, symbol=symbol, timeframe=timeframe, limit=limit)

    def latest_indicator_rows(self, timeframe: str) -> list[dict[str, Any]]:
        if self._session_factory is None:
            return []
        with self._session_factory() as session:
            rows = (
                session.query(IndicatorValueModel)
                .filter(IndicatorValueModel.timeframe == timeframe)
                .order_by(IndicatorValueModel.timestamp.desc())
                .limit(2000)
                .all()
            )
            latest_per_token: dict[str, dict[str, Any]] = {}
            for row in rows:
                if row.token in latest_per_token:
                    continue
                latest_per_token[row.token] = {
                    "token": row.token,
                    "rsi_14": row.rsi_14,
                    "ema_20": row.ema_20,
                    "macd": row.macd,
                    "macd_signal": row.macd_signal,
                    "iv": row.iv,
                    "oi": row.oi,
                }
            return list(latest_per_token.values())

    def latest_indicator_for_token(self, token: str, timeframe: str) -> dict[str, Any] | None:
        rows = self.latest_indicator_rows(timeframe=timeframe)
        for row in rows:
            if row.get("token") == token:
                return row
        return None

    def latest_and_previous_indicator_rows(self, timeframe: str) -> tuple[list[dict[str, Any]], dict[str, dict[str, Any]]]:
        if self._session_factory is None:
            return [], {}
        with self._session_factory() as session:
            rows = (
                session.query(IndicatorValueModel)
                .filter(IndicatorValueModel.timeframe == timeframe)
                .order_by(IndicatorValueModel.timestamp.desc())
                .limit(4000)
                .all()
            )
            latest: dict[str, dict[str, Any]] = {}
            previous: dict[str, dict[str, Any]] = {}
            for row in rows:
                token = row.token
                payload = {
                    "token": row.token,
                    "rsi_14": row.rsi_14,
                    "ema_20": row.ema_20,
                    "macd": row.macd,
                    "macd_signal": row.macd_signal,
                    "iv": row.iv,
                    "oi": row.oi,
                }
                if token not in latest:
                    latest[token] = payload
                elif token not in previous:
                    previous[token] = payload
            return list(latest.values()), previous

    @staticmethod
    def _latest_and_previous_for_token(session: Session, *, token: str, timeframe: str) -> tuple[dict[str, Any] | None, dict[str, Any] | None]:
        rows = (
            session.query(IndicatorValueModel)
            .filter(IndicatorValueModel.token == token)
            .filter(IndicatorValueModel.timeframe == timeframe)
            .order_by(IndicatorValueModel.timestamp.desc())
            .limit(2)
            .all()
        )
        if not rows:
            return None, None

        def _as_payload(row: IndicatorValueModel) -> dict[str, Any]:
            return {
                "token": row.token,
                "rsi_14": row.rsi_14,
                "ema_20": row.ema_20,
                "macd": row.macd,
                "macd_signal": row.macd_signal,
            }

        latest = _as_payload(rows[0])
        previous = _as_payload(rows[1]) if len(rows) > 1 else None
        return latest, previous


market_data_service = MarketDataService()
