from fastapi.testclient import TestClient
from uuid import uuid4

from app.main import app


client = TestClient(app)


def test_user_profile_and_preferences_flow() -> None:
    actor_id = f"clerk_user_{uuid4().hex[:8]}"
    headers = {"x-actor-id": actor_id}

    sync_response = client.post(
        "/api/v1/auth/sync",
        json={"email": "trader@example.com", "display_name": "Trader One"},
        headers=headers,
    )
    assert sync_response.status_code == 200
    assert sync_response.json()["clerk_user_id"] == actor_id
    assert sync_response.json()["email"] == "trader@example.com"

    user_response = client.get("/api/v1/user", headers=headers)
    assert user_response.status_code == 200
    assert user_response.json()["clerk_user_id"] == actor_id
    assert user_response.json()["display_name"] == "Trader One"

    user_alias_response = client.get("/api/v1/api/user", headers=headers)
    assert user_alias_response.status_code == 200
    assert user_alias_response.json()["clerk_user_id"] == actor_id

    user_put_response = client.put(
        "/api/v1/api/user",
        json={"email": "trader2@example.com", "display_name": "Trader Prime"},
        headers=headers,
    )
    assert user_put_response.status_code == 200
    assert user_put_response.json()["display_name"] == "Trader Prime"

    prefs_default = client.get("/api/v1/user/preferences", headers=headers)
    assert prefs_default.status_code == 200
    assert prefs_default.json()["default_timeframe"] == "5m"
    assert prefs_default.json()["default_indicator"] == "rsi_14"
    assert prefs_default.json()["theme"] == "dark"

    prefs_updated = client.put(
        "/api/v1/user/preferences",
        json={"default_timeframe": "15m", "default_indicator": "ema_20", "theme": "light"},
        headers=headers,
    )
    assert prefs_updated.status_code == 200
    assert prefs_updated.json()["default_timeframe"] == "15m"
    assert prefs_updated.json()["default_indicator"] == "ema_20"
    assert prefs_updated.json()["theme"] == "light"

    prefs_verify = client.get("/api/v1/user/preferences", headers=headers)
    assert prefs_verify.status_code == 200
    assert prefs_verify.json()["default_timeframe"] == "15m"
    assert prefs_verify.json()["default_indicator"] == "ema_20"
    assert prefs_verify.json()["theme"] == "light"
