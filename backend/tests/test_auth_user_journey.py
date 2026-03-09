from uuid import uuid4

from fastapi.testclient import TestClient

from app.main import app


def test_authenticated_user_journey_and_isolation() -> None:
    with TestClient(app) as client:
        user_a = f"user_{uuid4().hex[:8]}"
        user_b = f"user_{uuid4().hex[:8]}"

        unauth = client.get("/api/v1/user")
        assert unauth.status_code in {400, 401}

        a_headers = {"x-actor-id": user_a}
        b_headers = {"x-actor-id": user_b}

        a_sync = client.post(
            "/api/v1/auth/sync",
            json={"email": "alpha@example.com", "display_name": "Alpha"},
            headers=a_headers,
        )
        assert a_sync.status_code == 200
        assert a_sync.json()["clerk_user_id"] == user_a

        a_prefs = client.put(
            "/api/v1/user/preferences",
            json={"default_timeframe": "15m", "default_indicator": "ema_20", "theme": "light"},
            headers=a_headers,
        )
        assert a_prefs.status_code == 200
        assert a_prefs.json()["default_timeframe"] == "15m"

        b_default = client.get("/api/v1/user/preferences", headers=b_headers)
        assert b_default.status_code == 200
        assert b_default.json()["default_timeframe"] == "5m"
        assert b_default.json()["theme"] == "dark"

        create_watchlist = client.post(
            "/api/v1/watchlists",
            json={"user_id": user_a, "name": "Primary"},
        )
        assert create_watchlist.status_code == 200
        watchlist_id = create_watchlist.json()["id"]

        add_item = client.post(f"/api/v1/watchlists/{watchlist_id}/items", json={"token": "NIFTY_24000_CE"})
        assert add_item.status_code == 200

        user_a_watchlists = client.get("/api/v1/watchlists", params={"user_id": user_a})
        assert user_a_watchlists.status_code == 200
        assert len(user_a_watchlists.json()) >= 1

        user_b_watchlists = client.get("/api/v1/watchlists", params={"user_id": user_b})
        assert user_b_watchlists.status_code == 200
        assert user_b_watchlists.json() == []
