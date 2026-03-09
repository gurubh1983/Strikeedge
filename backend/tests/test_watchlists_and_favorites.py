from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import app


def test_watchlists_and_favorites_flow() -> None:
    with TestClient(app) as client:
        create_watchlist = client.post("/api/v1/watchlists", json={"user_id": "u-watch", "name": "My List"})
        assert create_watchlist.status_code == 200
        watchlist_id = create_watchlist.json()["id"]

        add_item = client.post(f"/api/v1/watchlists/{watchlist_id}/items", json={"token": "NIFTY_24000_CE"})
        assert add_item.status_code == 200
        assert "NIFTY_24000_CE" in add_item.json()["tokens"]

        list_watchlists = client.get("/api/v1/watchlists", params={"user_id": "u-watch"})
        assert list_watchlists.status_code == 200
        assert len(list_watchlists.json()) >= 1

        create_favorite = client.post("/api/v1/favorites", json={"user_id": "u-watch", "token": "NIFTY_24000_CE"})
        assert create_favorite.status_code == 200

        list_favorites = client.get("/api/v1/favorites", params={"user_id": "u-watch"})
        assert list_favorites.status_code == 200
        assert any(row["token"] == "NIFTY_24000_CE" for row in list_favorites.json())

        delete_favorite = client.delete("/api/v1/favorites", params={"user_id": "u-watch", "token": "NIFTY_24000_CE"})
        assert delete_favorite.status_code == 200
        assert delete_favorite.json()["deleted"] is True
