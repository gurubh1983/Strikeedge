from __future__ import annotations

from sqlalchemy.orm import Session, sessionmaker

from app.db.models import InstrumentModel


class InstrumentQueryService:
    def __init__(self) -> None:
        self._session_factory: sessionmaker[Session] | None = None

    def set_session_factory(self, session_factory: sessionmaker[Session]) -> None:
        self._session_factory = session_factory

    def list_instruments(self, limit: int = 200) -> list[dict]:
        if self._session_factory is None:
            return []
        with self._session_factory() as session:
            rows = session.query(InstrumentModel).limit(limit).all()
            return [{"token": row.token} for row in rows]

    def list_strikes(self, underlying: str, limit: int = 400) -> list[dict]:
        if self._session_factory is None:
            return []
        with self._session_factory() as session:
            rows = (
                session.query(InstrumentModel)
                .filter(InstrumentModel.underlying == underlying.upper())
                .limit(limit)
                .all()
            )
            return [{"token": row.token} for row in rows]

    def resolve_token(self, symbol_or_token: str) -> str:
        if self._session_factory is None:
            return symbol_or_token
        query = symbol_or_token.strip()
        if not query:
            return symbol_or_token
        with self._session_factory() as session:
            token_match = session.query(InstrumentModel).filter(InstrumentModel.token == query).first()
            if token_match is not None:
                return token_match.token
            symbol_match = session.query(InstrumentModel).filter(InstrumentModel.symbol == query).first()
            if symbol_match is not None:
                return symbol_match.token
        return symbol_or_token


instrument_query_service = InstrumentQueryService()
