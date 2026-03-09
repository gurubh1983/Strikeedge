from __future__ import annotations

import math

from sqlalchemy.orm import Session, sessionmaker

from app.db.models import CandleModel


class CorrelationService:
    def __init__(self) -> None:
        self._session_factory: sessionmaker[Session] | None = None

    def set_session_factory(self, session_factory: sessionmaker[Session]) -> None:
        self._session_factory = session_factory

    def price_correlation(self, *, token_a: str, token_b: str, timeframe: str = "5m", limit: int = 200) -> dict:
        if self._session_factory is None:
            return {"token_a": token_a, "token_b": token_b, "timeframe": timeframe, "samples": 0, "correlation": None}
        with self._session_factory() as session:
            rows_a = (
                session.query(CandleModel)
                .filter(CandleModel.token == token_a)
                .filter(CandleModel.timeframe == timeframe)
                .order_by(CandleModel.timestamp.desc())
                .limit(limit)
                .all()
            )
            rows_b = (
                session.query(CandleModel)
                .filter(CandleModel.token == token_b)
                .filter(CandleModel.timeframe == timeframe)
                .order_by(CandleModel.timestamp.desc())
                .limit(limit)
                .all()
            )
            map_a = {row.timestamp: float(row.close) for row in rows_a}
            map_b = {row.timestamp: float(row.close) for row in rows_b}
            common_ts = sorted(set(map_a.keys()) & set(map_b.keys()))
            xs = [map_a[ts] for ts in common_ts]
            ys = [map_b[ts] for ts in common_ts]
            corr = _pearson(xs, ys) if len(xs) >= 3 else None
            return {
                "token_a": token_a,
                "token_b": token_b,
                "timeframe": timeframe,
                "samples": len(xs),
                "correlation": round(corr, 6) if corr is not None else None,
            }


def _pearson(xs: list[float], ys: list[float]) -> float | None:
    if len(xs) != len(ys) or len(xs) < 2:
        return None
    mean_x = sum(xs) / len(xs)
    mean_y = sum(ys) / len(ys)
    num = sum((x - mean_x) * (y - mean_y) for x, y in zip(xs, ys))
    den_x = math.sqrt(sum((x - mean_x) ** 2 for x in xs))
    den_y = math.sqrt(sum((y - mean_y) ** 2 for y in ys))
    den = den_x * den_y
    if den == 0:
        return None
    return num / den


correlation_service = CorrelationService()
