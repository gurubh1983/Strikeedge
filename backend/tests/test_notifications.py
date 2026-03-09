from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import app
from app.services.notifications import notification_service


def test_notification_preference_and_outbox_flow() -> None:
    with TestClient(app) as client:
        pref = client.post(
            "/api/v1/notifications/preferences",
            json={"user_id": "u-notify", "channel": "email", "destination": "user@example.com", "enabled": True},
        )
        assert pref.status_code == 200
        pref_body = pref.json()
        assert pref_body["channel"] == "email"

        alert = client.post(
            "/api/v1/alerts",
            json={
                "user_id": "u-notify",
                "name": "Notify Alert",
                "rule": {"field": "rsi_14", "operator": ">", "value": 55},
            },
            headers={"x-actor-id": "u-notify", "x-idempotency-key": "notify-alert-1"},
        )
        assert alert.status_code == 200

        outbox = client.get("/api/v1/notifications/outbox", params={"user_id": "u-notify"})
        assert outbox.status_code == 200
        rows = outbox.json()
        assert len(rows) >= 1
        outbox_id = rows[0]["id"]

        dispatch = client.post(f"/api/v1/notifications/outbox/{outbox_id}/dispatch")
        assert dispatch.status_code == 200
        assert dispatch.json()["status"] == "sent"


def test_dispatch_pending_supports_failure_paths() -> None:
    with TestClient(app) as client:
        user_id = "u-notify-pending"
        client.post(
            "/api/v1/notifications/preferences",
            json={"user_id": user_id, "channel": "email", "destination": "bad-destination", "enabled": True},
        )
        alert = client.post(
            "/api/v1/alerts",
            json={
                "user_id": user_id,
                "name": "Pending Dispatch Alert",
                "rule": {"field": "rsi_14", "operator": ">", "value": 60},
            },
            headers={"x-actor-id": user_id, "x-idempotency-key": "notify-alert-pending-1"},
        )
        assert alert.status_code == 200

        def broken_email(_destination: str, _subject: str, _body: str) -> None:
            raise RuntimeError("Email provider unavailable")

        notification_service.set_dispatcher("email", broken_email)
        try:
            response = client.post("/api/v1/notifications/outbox/dispatch/pending", params={"limit": 20})
            assert response.status_code == 200
            body = response.json()
            assert body["processed"] >= 1
            assert body["failed"] >= 1
        finally:
            notification_service.reset_dispatchers()
