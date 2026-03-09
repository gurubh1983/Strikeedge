from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy.orm import Session, sessionmaker

from app.db.models import AlertModel, AuditEventModel, StrategyModel, WorkspaceModel


_TABLE_MODEL_MAP = {
    "strategies": StrategyModel,
    "workspaces": WorkspaceModel,
    "alerts": AlertModel,
    "audit": AuditEventModel,
}


class SqlAlchemyStore:
    def __init__(self, session_factory: sessionmaker[Session]) -> None:
        self.session_factory = session_factory

    def create(self, table: str, payload: dict[str, Any]) -> dict[str, Any]:
        model_cls = _TABLE_MODEL_MAP[table]
        with self.session_factory() as session:
            model = model_cls(**payload)
            session.add(model)
            session.commit()
            session.refresh(model)
            return self._serialize(model)

    def list(self, table: str, filters: dict[str, Any] | None = None) -> list[dict[str, Any]]:
        model_cls = _TABLE_MODEL_MAP[table]
        with self.session_factory() as session:
            query = session.query(model_cls)
            if filters:
                for key, value in filters.items():
                    if value is None:
                        continue
                    if hasattr(model_cls, key):
                        query = query.filter(getattr(model_cls, key) == value)
            rows = query.all()
            return [self._serialize(row) for row in rows]

    @staticmethod
    def _serialize(model: Any) -> dict[str, Any]:
        out: dict[str, Any] = {}
        for column in model.__table__.columns:  # type: ignore[attr-defined]
            value = getattr(model, column.name)
            if isinstance(value, datetime):
                out[column.name] = value.isoformat()
            else:
                out[column.name] = value
        return out
