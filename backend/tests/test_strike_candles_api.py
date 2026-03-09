from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from fastapi.testclient import TestClient

from app.db.models import InstrumentModel
from app.main import app


def test_strike_candle_accuracy_from_ticks() -> None:
    with TestClient(app) as client:
        token = "NIFTY_24000_CE_ACC"
        base = datetime(2026, 3, 8, 9, 15, tzinfo=timezone.utc)
        ticks = [
            (base.replace(second=1), 100.0, 10),
            (base.replace(second=10), 103.0, 20),
            (base.replace(second=20), 99.0, 30),
            (base.replace(second=40), 101.0, 40),
        ]
        for ts, ltp, volume in ticks:
            response = client.post(
                "/api/v1/internal/ticks",
                json={"token": token, "ltp": ltp, "volume": volume, "timeframe": "1m", "ts": ts.isoformat()},
                headers={"x-actor-id": "system"},
            )
            assert response.status_code == 200

        candles_response = client.get("/api/v1/strikes/NIFTY_24000_CE_ACC/candles", params={"timeframe": "1m", "limit": 1})
        assert candles_response.status_code == 200
        candles = candles_response.json()
        assert len(candles) == 1
        candle = candles[0]
        assert candle["open"] == 100.0
        assert candle["high"] == 103.0
        assert candle["low"] == 99.0
        assert candle["close"] == 101.0
        assert candle["volume"] == 100


def test_strike_symbol_to_token_mapping_for_candles() -> None:
    with TestClient(app) as client:
        suffix = uuid4().hex[:8].upper()
        token = f"TK-CE-{suffix}"
        symbol = f"NIFTY24APR24000CE{suffix}"

        session_factory = app.state.session_factory
        with session_factory() as session:
            session.add(
                InstrumentModel(
                    token=token,
                    symbol=symbol,
                    name="NIFTY",
                    exchange="NFO",
                    instrument_type="OPTIDX",
                    underlying="NIFTY",
                    option_type="CE",
                    strike_price=24000.0,
                    expiry="2026-04-24",
                    lot_size=50,
                )
            )
            session.commit()

        response = client.post(
            "/api/v1/internal/ticks",
            json={
                "token": token,
                "ltp": 111.0,
                "volume": 12,
                "timeframe": "1m",
                "ts": datetime(2026, 3, 8, 9, 16, tzinfo=timezone.utc).isoformat(),
            },
            headers={"x-actor-id": "system"},
        )
        assert response.status_code == 200

        candles_response = client.get(f"/api/v1/strikes/{symbol}/candles", params={"timeframe": "1m", "limit": 10})
        assert candles_response.status_code == 200
        candles = candles_response.json()
        assert candles
