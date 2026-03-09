from __future__ import annotations

from datetime import datetime, timedelta, timezone

from fastapi.testclient import TestClient

from app.main import app


def test_options_correlation_endpoint() -> None:
    base = datetime(2026, 3, 8, 9, 15, tzinfo=timezone.utc)
    with TestClient(app) as client:
        for i in range(20):
            t = (base + timedelta(minutes=i)).isoformat()
            a = 100 + i
            b = 200 + (i * 2)
            ra = client.post("/api/v1/internal/ticks", json={"token": "NIFTY", "ltp": a, "volume": 10, "timeframe": "5m", "ts": t}, headers={"x-actor-id": "system"})
            rb = client.post("/api/v1/internal/ticks", json={"token": "NIFTY_24000_CE", "ltp": b, "volume": 10, "timeframe": "5m", "ts": t}, headers={"x-actor-id": "system"})
            assert ra.status_code == 200
            assert rb.status_code == 200

        corr = client.get(
            "/api/v1/options/correlation",
            params={"token_a": "NIFTY", "token_b": "NIFTY_24000_CE", "timeframe": "5m", "limit": 100},
        )
        assert corr.status_code == 200
        body = corr.json()
        assert body["samples"] >= 3
        assert body["correlation"] is not None
