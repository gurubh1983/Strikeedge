from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy.orm import Session, sessionmaker

from app.db.models import SignalEventModel


class SignalDetector:
    def __init__(self) -> None:
        self._session_factory: sessionmaker[Session] | None = None

    def set_session_factory(self, session_factory: sessionmaker[Session]) -> None:
        self._session_factory = session_factory

    @staticmethod
    def detect_crossovers(token: str, timeframe: str, previous: dict | None, current: dict) -> list[dict]:
        if previous is None:
            return []
        events: list[dict] = []
        prev_rsi = previous.get("rsi_14")
        curr_rsi = current.get("rsi_14")
        if prev_rsi is not None and curr_rsi is not None:
            if float(prev_rsi) <= 60 and float(curr_rsi) > 60:
                events.append(
                    {
                        "token": token,
                        "timeframe": timeframe,
                        "signal_type": "crossover",
                        "indicator": "rsi_14",
                        "message": "RSI crossed above 60",
                    }
                )
            if float(prev_rsi) >= 40 and float(curr_rsi) < 40:
                events.append(
                    {
                        "token": token,
                        "timeframe": timeframe,
                        "signal_type": "crossover",
                        "indicator": "rsi_14",
                        "message": "RSI crossed below 40",
                    }
                )

        prev_macd = previous.get("macd")
        prev_signal = previous.get("macd_signal")
        curr_macd = current.get("macd")
        curr_signal = current.get("macd_signal")
        if None not in (prev_macd, prev_signal, curr_macd, curr_signal):
            if float(prev_macd) <= float(prev_signal) and float(curr_macd) > float(curr_signal):
                events.append(
                    {
                        "token": token,
                        "timeframe": timeframe,
                        "signal_type": "crossover",
                        "indicator": "macd",
                        "message": "MACD crossed above signal",
                    }
                )
            if float(prev_macd) >= float(prev_signal) and float(curr_macd) < float(curr_signal):
                events.append(
                    {
                        "token": token,
                        "timeframe": timeframe,
                        "signal_type": "crossover",
                        "indicator": "macd",
                        "message": "MACD crossed below signal",
                    }
                )
        return events

    def save_events(self, events: list[dict], session: Session | None = None) -> list[dict]:
        if not events:
            return []
        created_at = datetime.now(timezone.utc)
        if self._session_factory is None and session is None:
            return [dict(id=str(uuid4()), created_at=created_at.isoformat(), **event) for event in events]
        persisted: list[dict] = []
        if session is not None:
            for event in events:
                model = SignalEventModel(
                    id=str(uuid4()),
                    token=str(event["token"]),
                    timeframe=str(event["timeframe"]),
                    signal_type=str(event["signal_type"]),
                    indicator=str(event["indicator"]),
                    message=str(event["message"]),
                    created_at=created_at,
                )
                session.add(model)
                persisted.append(
                    {
                        "id": model.id,
                        "token": model.token,
                        "timeframe": model.timeframe,
                        "signal_type": model.signal_type,
                        "indicator": model.indicator,
                        "message": model.message,
                        "created_at": created_at.isoformat(),
                    }
                )
            return persisted

        with self._session_factory() as db_session:
            for event in events:
                model = SignalEventModel(
                    id=str(uuid4()),
                    token=str(event["token"]),
                    timeframe=str(event["timeframe"]),
                    signal_type=str(event["signal_type"]),
                    indicator=str(event["indicator"]),
                    message=str(event["message"]),
                    created_at=created_at,
                )
                db_session.add(model)
                persisted.append(
                    {
                        "id": model.id,
                        "token": model.token,
                        "timeframe": model.timeframe,
                        "signal_type": model.signal_type,
                        "indicator": model.indicator,
                        "message": model.message,
                        "created_at": created_at.isoformat(),
                    }
                )
            db_session.commit()
        return persisted

    def list_events(self, token: str | None = None, limit: int = 100) -> list[dict]:
        if self._session_factory is None:
            return []
        with self._session_factory() as session:
            query = session.query(SignalEventModel).order_by(SignalEventModel.created_at.desc())
            if token:
                query = query.filter(SignalEventModel.token == token)
            rows = query.limit(limit).all()
            return [
                {
                    "id": row.id,
                    "token": row.token,
                    "timeframe": row.timeframe,
                    "signal_type": row.signal_type,
                    "indicator": row.indicator,
                    "message": row.message,
                    "created_at": row.created_at.isoformat(),
                }
                for row in rows
            ]


signal_detector = SignalDetector()
