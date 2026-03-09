from __future__ import annotations

from datetime import datetime, timezone
from typing import Callable
from uuid import uuid4

from sqlalchemy.orm import Session, sessionmaker

from app.db.models import NotificationOutboxModel, NotificationPreferenceModel


class NotificationService:
    def __init__(self) -> None:
        self._session_factory: sessionmaker[Session] | None = None
        self._dispatchers: dict[str, Callable[[str, str, str], None]] = {
            "email": self._send_email,
            "push": self._send_push,
        }

    def set_session_factory(self, session_factory: sessionmaker[Session]) -> None:
        self._session_factory = session_factory

    def set_dispatcher(self, channel: str, dispatcher: Callable[[str, str, str], None]) -> None:
        self._dispatchers[channel] = dispatcher

    def reset_dispatchers(self) -> None:
        self._dispatchers = {
            "email": self._send_email,
            "push": self._send_push,
        }

    def upsert_preference(self, *, user_id: str, channel: str, destination: str, enabled: bool) -> dict:
        if self._session_factory is None:
            return {
                "id": str(uuid4()),
                "user_id": user_id,
                "channel": channel,
                "destination": destination,
                "enabled": enabled,
                "created_at": datetime.now(timezone.utc).isoformat(),
            }
        with self._session_factory() as session:
            row = (
                session.query(NotificationPreferenceModel)
                .filter(NotificationPreferenceModel.user_id == user_id)
                .filter(NotificationPreferenceModel.channel == channel)
                .first()
            )
            if row is None:
                row = NotificationPreferenceModel(
                    id=str(uuid4()),
                    user_id=user_id,
                    channel=channel,
                    destination=destination,
                    enabled=1 if enabled else 0,
                    created_at=datetime.now(timezone.utc),
                )
                session.add(row)
            else:
                row.destination = destination
                row.enabled = 1 if enabled else 0
            session.commit()
            return {
                "id": row.id,
                "user_id": row.user_id,
                "channel": row.channel,
                "destination": row.destination,
                "enabled": bool(row.enabled),
                "created_at": row.created_at.isoformat(),
            }

    def list_preferences(self, *, user_id: str) -> list[dict]:
        if self._session_factory is None:
            return []
        with self._session_factory() as session:
            rows = (
                session.query(NotificationPreferenceModel)
                .filter(NotificationPreferenceModel.user_id == user_id)
                .order_by(NotificationPreferenceModel.created_at.desc())
                .all()
            )
            return [
                {
                    "id": row.id,
                    "user_id": row.user_id,
                    "channel": row.channel,
                    "destination": row.destination,
                    "enabled": bool(row.enabled),
                    "created_at": row.created_at.isoformat(),
                }
                for row in rows
            ]

    def queue_alert_notification(self, *, user_id: str, subject: str, body: str) -> list[dict]:
        if self._session_factory is None:
            return []
        with self._session_factory() as session:
            prefs = (
                session.query(NotificationPreferenceModel)
                .filter(NotificationPreferenceModel.user_id == user_id)
                .filter(NotificationPreferenceModel.enabled == 1)
                .all()
            )
            queued: list[dict] = []
            for pref in prefs:
                outbox = NotificationOutboxModel(
                    id=str(uuid4()),
                    user_id=user_id,
                    channel=pref.channel,
                    destination=pref.destination,
                    subject=subject,
                    body=body,
                    status="pending",
                    error_message=None,
                    created_at=datetime.now(timezone.utc),
                    sent_at=None,
                )
                session.add(outbox)
                queued.append(
                    {
                        "id": outbox.id,
                        "user_id": outbox.user_id,
                        "channel": outbox.channel,
                        "destination": outbox.destination,
                        "subject": outbox.subject,
                        "body": outbox.body,
                        "status": outbox.status,
                        "error_message": outbox.error_message,
                        "created_at": outbox.created_at.isoformat(),
                        "sent_at": None,
                    }
                )
            session.commit()
            return queued

    def list_outbox(self, *, user_id: str, limit: int = 100) -> list[dict]:
        if self._session_factory is None:
            return []
        with self._session_factory() as session:
            rows = (
                session.query(NotificationOutboxModel)
                .filter(NotificationOutboxModel.user_id == user_id)
                .order_by(NotificationOutboxModel.created_at.desc())
                .limit(limit)
                .all()
            )
            return [
                {
                    "id": row.id,
                    "user_id": row.user_id,
                    "channel": row.channel,
                    "destination": row.destination,
                    "subject": row.subject,
                    "body": row.body,
                    "status": row.status,
                    "error_message": row.error_message,
                    "created_at": row.created_at.isoformat(),
                    "sent_at": row.sent_at.isoformat() if row.sent_at else None,
                }
                for row in rows
            ]

    def dispatch_outbox_item(self, *, outbox_id: str) -> dict | None:
        if self._session_factory is None:
            return None
        with self._session_factory() as session:
            row = session.get(NotificationOutboxModel, outbox_id)
            if row is None:
                return None
            dispatcher = self._dispatchers.get(row.channel)
            if dispatcher is None:
                row.status = "failed"
                row.error_message = f"Unsupported channel: {row.channel}"
                row.sent_at = None
            else:
                try:
                    dispatcher(row.destination, row.subject, row.body)
                    row.status = "sent"
                    row.sent_at = datetime.now(timezone.utc)
                    row.error_message = None
                except Exception as exc:
                    row.status = "failed"
                    row.error_message = str(exc)
                    row.sent_at = None
            session.commit()
            return {
                "id": row.id,
                "user_id": row.user_id,
                "channel": row.channel,
                "destination": row.destination,
                "subject": row.subject,
                "body": row.body,
                "status": row.status,
                "error_message": row.error_message,
                "created_at": row.created_at.isoformat(),
                "sent_at": row.sent_at.isoformat() if row.sent_at else None,
            }

    def dispatch_pending(self, *, limit: int = 100) -> dict[str, int]:
        if self._session_factory is None:
            return {"processed": 0, "sent": 0, "failed": 0}
        with self._session_factory() as session:
            rows = (
                session.query(NotificationOutboxModel)
                .filter(NotificationOutboxModel.status == "pending")
                .order_by(NotificationOutboxModel.created_at.asc())
                .limit(limit)
                .all()
            )
            ids = [row.id for row in rows]
        sent = 0
        failed = 0
        for outbox_id in ids:
            row = self.dispatch_outbox_item(outbox_id=outbox_id)
            if not row:
                continue
            if row["status"] == "sent":
                sent += 1
            elif row["status"] == "failed":
                failed += 1
        return {"processed": len(ids), "sent": sent, "failed": failed}

    @staticmethod
    def _send_email(destination: str, subject: str, body: str) -> None:
        if not destination:
            raise ValueError("Email destination is required")
        _ = (subject, body)

    @staticmethod
    def _send_push(destination: str, subject: str, body: str) -> None:
        if not destination:
            raise ValueError("Push destination is required")
        _ = (subject, body)


notification_service = NotificationService()
