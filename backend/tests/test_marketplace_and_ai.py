from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import app


def test_ai_sentiment_and_patterns_endpoints() -> None:
    with TestClient(app) as client:
        sentiment = client.get("/api/v1/ai/sentiment/NIFTY")
        assert sentiment.status_code == 200
        sent_body = sentiment.json()
        assert sent_body["symbol"] == "NIFTY"
        assert sent_body["sentiment"] in {"bullish", "bearish", "neutral"}

        patterns = client.get("/api/v1/ai/patterns/NIFTY", params={"timeframe": "5m"})
        assert patterns.status_code == 200
        pattern_body = patterns.json()
        assert pattern_body["symbol"] == "NIFTY"
        assert isinstance(pattern_body["signals"], list)


def test_marketplace_publish_list_share() -> None:
    with TestClient(app) as client:
        publish = client.post(
            "/api/v1/marketplace/publish",
            json={
                "strategy_id": "strategy-123",
                "owner_id": "owner-1",
                "title": "Momentum Breakout v1",
                "description": "Breakout strategy with momentum confirmation",
                "tags": ["momentum", "breakout"],
            },
        )
        assert publish.status_code == 200
        body = publish.json()
        assert body["title"] == "Momentum Breakout v1"
        share_code = body["share_code"]

        listing = client.get("/api/v1/marketplace/strategies", params={"limit": 10})
        assert listing.status_code == 200
        assert any(row["share_code"] == share_code for row in listing.json())

        shared = client.get(f"/api/v1/marketplace/share/{share_code}")
        assert shared.status_code == 200
        assert shared.json()["share_code"] == share_code
