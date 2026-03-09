from __future__ import annotations

from datetime import datetime, timedelta, timezone

from fastapi.testclient import TestClient

from app.main import app


def test_tick_ingest_persists_candle_and_chart() -> None:
    client = TestClient(app)
    token = "NIFTY_24000_CE"
    for price in [100.0, 101.0, 99.5, 102.0]:
        response = client.post(
            "/api/v1/internal/ticks",
            json={"token": token, "ltp": price, "volume": 10, "timeframe": "1m"},
            headers={"x-actor-id": "system"},
        )
        assert response.status_code == 200
        assert response.json()["ingested"] is True

    chart_response = client.get(f"/api/v1/chart/{token}")
    assert chart_response.status_code == 200
    body = chart_response.json()
    assert body["token"] == token
    assert "candles" in body


def test_scan_works_after_tick_ingestion() -> None:
    client = TestClient(app)
    token = "NIFTY_24000_PE"
    base = datetime(2026, 3, 8, 9, 15, tzinfo=timezone.utc)
    for idx, price in enumerate([90.0, 91.0, 92.0, 93.0, 94.0, 95.0, 96.0, 97.0, 98.0, 99.0, 100.0, 101.0, 102.0, 103.0, 104.0, 105.0, 106.0]):
        response = client.post(
            "/api/v1/internal/ticks",
            json={
                "token": token,
                "ltp": price,
                "volume": 5,
                "timeframe": "1m",
                "ts": (base + timedelta(minutes=idx)).isoformat(),
            },
            headers={"x-actor-id": "system"},
        )
        assert response.status_code == 200

    scan_response = client.post(
        "/api/v1/scan",
        json={"timeframe": "1m", "rules": [{"field": "rsi_14", "operator": ">", "value": 10}]},
        headers={"x-actor-id": "scan-user"},
    )
    assert scan_response.status_code == 200
    assert "scan_id" in scan_response.json()
