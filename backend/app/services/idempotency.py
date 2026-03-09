from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy.orm import Session, sessionmaker

from app.core.metrics import metrics_registry
from app.core.settings import get_settings
from app.db.models import IdempotencyRecordModel


class IdempotencyService:
    def __init__(self) -> None:
        self._session_factory: sessionmaker[Session] | None = None
        self._memory: dict[tuple[str, str, str], dict] = {}

    def set_session_factory(self, session_factory: sessionmaker[Session]) -> None:
        self._session_factory = session_factory

    def fetch(self, actor_id: str, idempotency_key: str, endpoint: str) -> dict | None:
        key = (actor_id, idempotency_key, endpoint)
        settings = get_settings()
        cutoff = datetime.now(timezone.utc).timestamp() - settings.idempotency_ttl_seconds
        if self._session_factory is None:
            payload = self._memory.get(key)
            if payload is None:
                return None
            created_at = payload.get("_created_at")
            if isinstance(created_at, (int, float)) and created_at < cutoff:
                self._memory.pop(key, None)
                return None
            return payload.get("response")

        with self._session_factory() as session:
            row = (
                session.query(IdempotencyRecordModel)
                .filter(IdempotencyRecordModel.actor_id == actor_id)
                .filter(IdempotencyRecordModel.idempotency_key == idempotency_key)
                .filter(IdempotencyRecordModel.endpoint == endpoint)
                .order_by(IdempotencyRecordModel.created_at.desc())
                .first()
            )
            if row is None:
                return None
            if row.created_at.timestamp() < cutoff:
                return None
            return row.response_payload

    def store(self, actor_id: str, idempotency_key: str, endpoint: str, payload: dict) -> dict:
        key = (actor_id, idempotency_key, endpoint)
        if self._session_factory is None:
            self._memory[key] = {
                "response": payload,
                "_created_at": datetime.now(timezone.utc).timestamp(),
            }
            metrics_registry.incr("service_idempotency_store_total")
            return payload

        with self._session_factory() as session:
            row = IdempotencyRecordModel(
                id=str(uuid4()),
                actor_id=actor_id,
                idempotency_key=idempotency_key,
                endpoint=endpoint,
                response_payload=payload,
                created_at=datetime.now(timezone.utc),
            )
            session.add(row)
            session.commit()
            metrics_registry.incr("service_idempotency_store_total")
            return payload

    def cleanup_expired(self) -> int:
        settings = get_settings()
        now = datetime.now(timezone.utc).timestamp()
        cutoff_ts = now - settings.idempotency_ttl_seconds
        cleaned = 0
        if self._session_factory is None:
            to_delete = [key for key, value in self._memory.items() if float(value.get("_created_at", 0)) < cutoff_ts]
            for key in to_delete:
                self._memory.pop(key, None)
                cleaned += 1
            if cleaned:
                metrics_registry.incr("service_idempotency_cleanup_total", cleaned)
            return cleaned

        cutoff_dt = datetime.fromtimestamp(cutoff_ts, tz=timezone.utc)
        with self._session_factory() as session:
            rows = session.query(IdempotencyRecordModel).filter(IdempotencyRecordModel.created_at < cutoff_dt).all()
            cleaned = len(rows)
            for row in rows:
                session.delete(row)
            session.commit()
        if cleaned:
            metrics_registry.incr("service_idempotency_cleanup_total", cleaned)
        return cleaned


idempotency_service = IdempotencyService()
