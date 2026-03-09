from __future__ import annotations

import re
from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy.orm import Session, sessionmaker

from app.db.models import OIHistoryModel, OptionsChainModel, StrikeGreeksModel
from app.services.options_analytics import options_analytics_service


_SYMBOL_STRIKE_RE = re.compile(r"(\d{3,6})(CE|PE)$", re.IGNORECASE)


def _parse_strike_from_symbol(symbol: str) -> float | None:
    match = _SYMBOL_STRIKE_RE.search(symbol.replace(" ", ""))
    if not match:
        return None
    return float(match.group(1))


class OptionsVolatilityService:
    def __init__(self) -> None:
        self._session_factory: sessionmaker[Session] | None = None

    def set_session_factory(self, session_factory: sessionmaker[Session]) -> None:
        self._session_factory = session_factory

    def calculate_greeks_for_chain(
        self,
        *,
        underlying: str,
        expiry: str,
        spot: float,
        time_to_expiry_years: float,
        risk_free_rate: float = 0.06,
    ) -> int:
        if self._session_factory is None:
            return 0
        upserted = 0
        with self._session_factory() as session:
            rows = (
                session.query(OptionsChainModel)
                .filter(OptionsChainModel.underlying == underlying.upper())
                .filter(OptionsChainModel.expiry == expiry)
                .all()
            )
            for row in rows:
                legs = [
                    ("CE", row.call_symbol, row.call_token, row.call_iv),
                    ("PE", row.put_symbol, row.put_token, row.put_iv),
                ]
                for option_type, symbol, token, iv in legs:
                    if not symbol or not token:
                        continue
                    volatility = max(float((iv or 20.0)) / 100.0, 0.01)
                    values = options_analytics_service.greeks(
                        option_type=option_type,
                        spot=spot,
                        strike=float(row.strike_price),
                        time_to_expiry_years=time_to_expiry_years,
                        risk_free_rate=risk_free_rate,
                        volatility=volatility,
                    )
                    model = (
                        session.query(StrikeGreeksModel)
                        .filter(StrikeGreeksModel.token == token)
                        .filter(StrikeGreeksModel.expiry == expiry)
                        .first()
                    )
                    if model is None:
                        model = StrikeGreeksModel(
                            id=str(uuid4()),
                            underlying=underlying.upper(),
                            expiry=expiry,
                            symbol=symbol,
                            token=token,
                            option_type=option_type,
                            strike_price=float(row.strike_price),
                            spot=spot,
                            time_to_expiry_years=time_to_expiry_years,
                            risk_free_rate=risk_free_rate,
                            volatility=volatility,
                            delta=values["delta"],
                            gamma=values["gamma"],
                            theta=values["theta"],
                            vega=values["vega"],
                            rho=values["rho"],
                            calculated_at=datetime.now(timezone.utc),
                        )
                        session.add(model)
                    else:
                        model.symbol = symbol
                        model.underlying = underlying.upper()
                        model.option_type = option_type
                        model.strike_price = float(row.strike_price)
                        model.spot = spot
                        model.time_to_expiry_years = time_to_expiry_years
                        model.risk_free_rate = risk_free_rate
                        model.volatility = volatility
                        model.delta = values["delta"]
                        model.gamma = values["gamma"]
                        model.theta = values["theta"]
                        model.vega = values["vega"]
                        model.rho = values["rho"]
                        model.calculated_at = datetime.now(timezone.utc)
                    upserted += 1
            session.commit()
        return upserted

    def get_symbol_greeks(self, *, symbol: str) -> dict | None:
        if self._session_factory is None:
            return None
        with self._session_factory() as session:
            row = (
                session.query(StrikeGreeksModel)
                .filter(StrikeGreeksModel.symbol == symbol)
                .order_by(StrikeGreeksModel.calculated_at.desc())
                .first()
            )
            if row is None:
                return None
            return {
                "underlying": row.underlying,
                "expiry": row.expiry,
                "symbol": row.symbol,
                "token": row.token,
                "option_type": row.option_type,
                "strike_price": row.strike_price,
                "spot": row.spot,
                "time_to_expiry_years": row.time_to_expiry_years,
                "risk_free_rate": row.risk_free_rate,
                "volatility": row.volatility,
                "delta": row.delta,
                "gamma": row.gamma,
                "theta": row.theta,
                "vega": row.vega,
                "rho": row.rho,
                "calculated_at": row.calculated_at.isoformat(),
            }

    def capture_oi_history(
        self,
        *,
        underlying: str,
        expiry: str,
        strike_price: float,
        call_oi: int,
        put_oi: int,
        session: Session | None = None,
    ) -> None:
        if self._session_factory is None and session is None:
            return
        owns_session = session is None
        if session is None:
            session = self._session_factory()  # type: ignore[operator]
        try:
            total_oi = int(call_oi + put_oi)
            previous = (
                session.query(OIHistoryModel)  # type: ignore[union-attr]
                .filter(OIHistoryModel.underlying == underlying.upper())
                .filter(OIHistoryModel.expiry == expiry)
                .filter(OIHistoryModel.strike_price == float(strike_price))
                .order_by(OIHistoryModel.recorded_at.desc())
                .first()
            )
            previous_total = int(previous.total_oi) if previous else 0
            change = total_oi - previous_total
            change_pct = (float(change) / float(previous_total) * 100.0) if previous_total > 0 else 0.0
            session.add(  # type: ignore[union-attr]
                OIHistoryModel(
                    id=str(uuid4()),
                    underlying=underlying.upper(),
                    expiry=expiry,
                    strike_price=float(strike_price),
                    call_oi=call_oi,
                    put_oi=put_oi,
                    total_oi=total_oi,
                    total_oi_change=change,
                    total_oi_change_pct=round(change_pct, 4),
                    recorded_at=datetime.now(timezone.utc),
                )
            )
            if owns_session:
                session.commit()  # type: ignore[union-attr]
        finally:
            if owns_session:
                session.close()  # type: ignore[union-attr]

    def oi_heatmap(self, *, underlying: str, expiry: str, limit: int = 200) -> list[dict]:
        if self._session_factory is None:
            return []
        with self._session_factory() as session:
            rows = (
                session.query(OIHistoryModel)
                .filter(OIHistoryModel.underlying == underlying.upper())
                .filter(OIHistoryModel.expiry == expiry)
                .order_by(OIHistoryModel.recorded_at.desc())
                .limit(limit)
                .all()
            )
            return [
                {
                    "strike_price": row.strike_price,
                    "total_oi": row.total_oi,
                    "total_oi_change": row.total_oi_change,
                    "total_oi_change_pct": row.total_oi_change_pct,
                    "recorded_at": row.recorded_at.isoformat(),
                }
                for row in rows
            ]

    def oi_spikes(self, *, underlying: str, expiry: str, threshold_pct: float = 20.0, limit: int = 100) -> list[dict]:
        rows = self.oi_heatmap(underlying=underlying, expiry=expiry, limit=limit)
        return [row for row in rows if abs(float(row["total_oi_change_pct"])) >= threshold_pct]

    def portfolio_greeks(self, *, underlying: str, expiry: str = "") -> dict:
        """Sum delta, gamma, theta, vega across all strikes for the underlying."""
        if self._session_factory is None:
            return {"delta": 0.0, "gamma": 0.0, "theta": 0.0, "vega": 0.0, "count": 0}
        with self._session_factory() as session:
            q = (
                session.query(StrikeGreeksModel)
                .filter(StrikeGreeksModel.underlying == underlying.upper())
            )
            if expiry:
                q = q.filter(StrikeGreeksModel.expiry == expiry)
            rows = q.all()
        delta = sum(float(r.delta) for r in rows)
        gamma = sum(float(r.gamma) for r in rows)
        theta = sum(float(r.theta) for r in rows)
        vega = sum(float(r.vega) for r in rows)
        return {
            "delta": round(delta, 4),
            "gamma": round(gamma, 6),
            "theta": round(theta, 2),
            "vega": round(vega, 2),
            "count": len(rows),
        }

    @staticmethod
    def derive_moneyness(*, symbol: str, spot: float) -> float:
        strike = _parse_strike_from_symbol(symbol)
        if strike is None or spot <= 0:
            return 0.0
        return round((strike - spot) / spot * 100.0, 4)


options_volatility_service = OptionsVolatilityService()
