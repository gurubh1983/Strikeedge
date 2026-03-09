from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy.orm import Session, sessionmaker

from app.db.models import ScreenerModel
from app.schemas import ScreenerIn, ScreenerUpdateIn


class ScreenerStoreService:
    def __init__(self) -> None:
        self._session_factory: sessionmaker[Session] | None = None
        self._memory: dict[str, dict] = {}

    def set_session_factory(self, session_factory: sessionmaker[Session]) -> None:
        self._session_factory = session_factory

    def create(self, payload: ScreenerIn) -> dict:
        screener_id = str(uuid4())
        row = {
            "id": screener_id,
            "user_id": payload.user_id,
            "name": payload.name,
            "description": payload.description,
            "underlying": payload.underlying,
            "timeframe": payload.timeframe,
            "groups": [group.model_dump() for group in payload.groups],
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        if self._session_factory is None:
            self._memory[screener_id] = row
            return row
        with self._session_factory() as session:
            session.add(
                ScreenerModel(
                    id=screener_id,
                    user_id=payload.user_id,
                    name=payload.name,
                    description=payload.description,
                    timeframe=payload.timeframe,
                    conditions=[group.model_dump() for group in payload.groups],
                    created_at=datetime.now(timezone.utc),
                )
            )
            session.commit()
        return row

    def list(self, user_id: str | None = None) -> list[dict]:
        if self._session_factory is None:
            rows = list(self._memory.values())
            if user_id:
                rows = [row for row in rows if row["user_id"] == user_id]
            return rows
        with self._session_factory() as session:
            query = session.query(ScreenerModel).order_by(ScreenerModel.created_at.desc())
            if user_id:
                query = query.filter(ScreenerModel.user_id == user_id)
            rows = query.all()
            return [
                {
                    "id": row.id,
                    "user_id": row.user_id,
                    "name": row.name,
                    "description": row.description,
                    "underlying": None,
                    "timeframe": row.timeframe,
                    "groups": row.conditions,
                    "created_at": row.created_at.isoformat(),
                }
                for row in rows
            ]

    def get(self, screener_id: str) -> dict | None:
        if self._session_factory is None:
            return self._memory.get(screener_id)
        with self._session_factory() as session:
            row = session.get(ScreenerModel, screener_id)
            if row is None:
                return None
            return {
                "id": row.id,
                "user_id": row.user_id,
                "name": row.name,
                "description": row.description,
                "underlying": None,
                "timeframe": row.timeframe,
                "groups": row.conditions,
                "created_at": row.created_at.isoformat(),
            }

    def update(self, screener_id: str, payload: ScreenerUpdateIn) -> dict | None:
        if self._session_factory is None:
            existing = self._memory.get(screener_id)
            if existing is None:
                return None
            patch = payload.model_dump(exclude_none=True)
            if "groups" in patch:
                patch["groups"] = [group.model_dump() for group in payload.groups or []]
            existing.update(patch)
            return existing
        with self._session_factory() as session:
            row = session.get(ScreenerModel, screener_id)
            if row is None:
                return None
            if payload.name is not None:
                row.name = payload.name
            if payload.description is not None:
                row.description = payload.description
            if payload.timeframe is not None:
                row.timeframe = payload.timeframe
            if payload.groups is not None:
                row.conditions = [group.model_dump() for group in payload.groups]
            session.commit()
            return {
                "id": row.id,
                "user_id": row.user_id,
                "name": row.name,
                "description": row.description,
                "underlying": None,
                "timeframe": row.timeframe,
                "groups": row.conditions,
                "created_at": row.created_at.isoformat(),
            }

    def delete(self, screener_id: str) -> bool:
        if self._session_factory is None:
            return self._memory.pop(screener_id, None) is not None
        with self._session_factory() as session:
            row = session.get(ScreenerModel, screener_id)
            if row is None:
                return False
            session.delete(row)
            session.commit()
            return True


screener_store_service = ScreenerStoreService()
