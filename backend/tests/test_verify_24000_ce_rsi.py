from __future__ import annotations

from datetime import datetime, timedelta, timezone

from fastapi.testclient import TestClient

from app.main import app


def test_verify_24000_ce_rsi_pipeline() -> None:
    token = "NIFTY_24000_CE"
    base = datetime(2026, 3, 8, 9, 15, tzinfo=timezone.utc)

    with TestClient(app) as client:
        # Feed enough candles to compute RSI(14) snapshot.
        for idx in range(20):
            client.post(
                "/api/v1/internal/ticks",
                json={
                    "token": token,
                    "ltp": 100 + idx,
                    "volume": 10,
                    "timeframe": "1m",
                    "ts": (base + timedelta(minutes=idx)).isoformat(),
                },
                headers={"x-actor-id": "system"},
            )

        indicator_response = client.get(f"/api/v1/internal/indicators/{token}", params={"timeframe": "1m"})
        assert indicator_response.status_code == 200
        payload = indicator_response.json()
        assert payload["indicator"] is not None
        assert payload["indicator"]["rsi_14"] is not None
        assert 0 <= float(payload["indicator"]["rsi_14"]) <= 100
