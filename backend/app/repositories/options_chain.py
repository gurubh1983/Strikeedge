from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy.orm import Session, sessionmaker

from app.db.models import OptionsChainModel
from app.services.options_volatility import options_volatility_service


class OptionsChainRepository:
    def __init__(self, session_factory: sessionmaker[Session]) -> None:
        self.session_factory = session_factory

    def upsert_chain(self, *, underlying: str, expiry: str, rows: list[dict]) -> int:
        upserted = 0
        with self.session_factory() as session:
            for row in rows:
                existing = (
                    session.query(OptionsChainModel)
                    .filter(OptionsChainModel.underlying == underlying)
                    .filter(OptionsChainModel.expiry == expiry)
                    .filter(OptionsChainModel.strike_price == float(row["strike_price"]))
                    .first()
                )
                if existing is None:
                    existing = OptionsChainModel(
                        id=str(uuid4()),
                        underlying=underlying,
                        expiry=expiry,
                        strike_price=float(row["strike_price"]),
                        call_token=row.get("call_token"),
                        call_symbol=row.get("call_symbol"),
                        call_oi=row.get("call_oi"),
                        call_iv=row.get("call_iv"),
                        put_token=row.get("put_token"),
                        put_symbol=row.get("put_symbol"),
                        put_oi=row.get("put_oi"),
                        put_iv=row.get("put_iv"),
                        put_call_ratio=row.get("put_call_ratio"),
                        total_oi_change=None,
                        lot_size=int(row.get("lot_size") or 1),
                        fetched_at=datetime.now(timezone.utc),
                    )
                    session.add(existing)
                    options_volatility_service.capture_oi_history(
                        underlying=underlying,
                        expiry=expiry,
                        strike_price=float(row["strike_price"]),
                        call_oi=int(row.get("call_oi") or 0),
                        put_oi=int(row.get("put_oi") or 0),
                        session=session,
                    )
                else:
                    previous_total = int((existing.call_oi or 0) + (existing.put_oi or 0))
                    existing.call_token = row.get("call_token")
                    existing.call_symbol = row.get("call_symbol")
                    existing.call_oi = row.get("call_oi")
                    existing.call_iv = row.get("call_iv")
                    existing.put_token = row.get("put_token")
                    existing.put_symbol = row.get("put_symbol")
                    existing.put_oi = row.get("put_oi")
                    existing.put_iv = row.get("put_iv")
                    existing.put_call_ratio = row.get("put_call_ratio")
                    current_total = int((existing.call_oi or 0) + (existing.put_oi or 0))
                    existing.total_oi_change = current_total - previous_total
                    existing.lot_size = int(row.get("lot_size") or 1)
                    existing.fetched_at = datetime.now(timezone.utc)
                    options_volatility_service.capture_oi_history(
                        underlying=underlying,
                        expiry=expiry,
                        strike_price=float(row["strike_price"]),
                        call_oi=int(existing.call_oi or 0),
                        put_oi=int(existing.put_oi or 0),
                        session=session,
                    )
                upserted += 1
            session.commit()
        return upserted

    def list_chain(self, *, underlying: str, expiry: str, limit: int = 200) -> list[dict]:
        with self.session_factory() as session:
            rows = (
                session.query(OptionsChainModel)
                .filter(OptionsChainModel.underlying == underlying)
                .filter(OptionsChainModel.expiry == expiry)
                .order_by(OptionsChainModel.strike_price.asc())
                .limit(limit)
                .all()
            )
            return [
                {
                    "underlying": row.underlying,
                    "expiry": row.expiry,
                    "strike_price": row.strike_price,
                    "call_token": row.call_token,
                    "call_symbol": row.call_symbol,
                    "call_oi": row.call_oi,
                    "call_iv": row.call_iv,
                    "put_token": row.put_token,
                    "put_symbol": row.put_symbol,
                    "put_oi": row.put_oi,
                    "put_iv": row.put_iv,
                    "put_call_ratio": row.put_call_ratio,
                    "total_oi_change": row.total_oi_change,
                    "lot_size": row.lot_size,
                    "fetched_at": row.fetched_at.isoformat(),
                }
                for row in rows
            ]

    def get_chain_metrics(self, *, underlying: str, expiry: str) -> dict:
        with self.session_factory() as session:
            rows = (
                session.query(OptionsChainModel)
                .filter(OptionsChainModel.underlying == underlying)
                .filter(OptionsChainModel.expiry == expiry)
                .all()
            )
            if not rows:
                return {
                    "underlying": underlying,
                    "expiry": expiry,
                    "strikes": 0,
                    "total_call_oi": 0,
                    "total_put_oi": 0,
                    "put_call_ratio": None,
                    "total_oi_change": 0,
                }
            total_call_oi = sum(int(row.call_oi or 0) for row in rows)
            total_put_oi = sum(int(row.put_oi or 0) for row in rows)
            pcr = round(float(total_put_oi) / float(total_call_oi), 4) if total_call_oi > 0 else None
            total_oi_change = sum(int(row.total_oi_change or 0) for row in rows)
            return {
                "underlying": underlying,
                "expiry": expiry,
                "strikes": len(rows),
                "total_call_oi": total_call_oi,
                "total_put_oi": total_put_oi,
                "put_call_ratio": pcr,
                "total_oi_change": total_oi_change,
            }
