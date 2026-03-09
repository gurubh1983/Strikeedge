from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import app
from app.services.options_chain import options_chain_service


class FakeFyersClientPhase3:
    async def fetch_scrip_master(self) -> list[dict]:
        return [
            {
                "exch_seg": "NFO",
                "instrumenttype": "OPTIDX",
                "symbol": "NIFTY24APR24000CE",
                "name": "NIFTY",
                "expiry": "2026-04-24",
                "strike": "2400000",
                "token": "311",
                "lotsize": 50,
                "oi": "12500",
                "iv": "16.0",
            },
            {
                "exch_seg": "NFO",
                "instrumenttype": "OPTIDX",
                "symbol": "NIFTY24APR24000PE",
                "name": "NIFTY",
                "expiry": "2026-04-24",
                "strike": "2400000",
                "token": "312",
                "lotsize": 50,
                "oi": "13200",
                "iv": "17.0",
            },
        ]

    @staticmethod
    def build_options_chain(records: list[dict], *, underlying: str, expiry: str) -> list[dict]:
        from app.data_pipeline.fyers_client import FyersClient

        return FyersClient.build_options_chain(records, underlying=underlying, expiry=expiry)


class FakeFyersClientPhase3Mutable:
    def __init__(self) -> None:
        self.call_oi = 10000
        self.put_oi = 12000

    async def fetch_scrip_master(self) -> list[dict]:
        return [
            {
                "exch_seg": "NFO",
                "instrumenttype": "OPTIDX",
                "symbol": "NIFTY24APR24000CE",
                "name": "NIFTY",
                "expiry": "2026-04-24",
                "strike": "2400000",
                "token": "411",
                "lotsize": 50,
                "oi": str(self.call_oi),
                "iv": "16.0",
            },
            {
                "exch_seg": "NFO",
                "instrumenttype": "OPTIDX",
                "symbol": "NIFTY24APR24000PE",
                "name": "NIFTY",
                "expiry": "2026-04-24",
                "strike": "2400000",
                "token": "412",
                "lotsize": 50,
                "oi": str(self.put_oi),
                "iv": "17.0",
            },
        ]

    @staticmethod
    def build_options_chain(records: list[dict], *, underlying: str, expiry: str) -> list[dict]:
        from app.data_pipeline.fyers_client import FyersClient

        return FyersClient.build_options_chain(records, underlying=underlying, expiry=expiry)


def test_phase3_greeks_batch_and_symbol_endpoint() -> None:
    original_client = options_chain_service.fyers_client
    options_chain_service.fyers_client = FakeFyersClientPhase3()  # type: ignore[assignment]
    try:
        with TestClient(app) as client:
            refresh = client.get(
                "/api/v1/options/chain",
                params={"underlying": "NIFTY", "expiry": "2026-04-24", "refresh": True},
            )
            assert refresh.status_code == 200

            calc = client.post(
                "/api/v1/options/greeks/calculate",
                params={
                    "underlying": "NIFTY",
                    "expiry": "2026-04-24",
                    "spot": 24000,
                    "time_to_expiry_years": 20 / 365,
                },
            )
            assert calc.status_code == 200
            assert calc.json()["calculated"] >= 2

            symbol = "NIFTY24APR24000CE"
            by_symbol = client.get(f"/api/v1/strikes/{symbol}/vol/greeks")
            assert by_symbol.status_code == 200
            body = by_symbol.json()
            assert body["symbol"] == symbol
            assert "delta" in body
    finally:
        options_chain_service.fyers_client = original_client


def test_phase3_oi_tracking_accuracy_change_percentage() -> None:
    original_client = options_chain_service.fyers_client
    fake = FakeFyersClientPhase3Mutable()
    options_chain_service.fyers_client = fake  # type: ignore[assignment]
    try:
        with TestClient(app) as client:
            first = client.get(
                "/api/v1/options/chain",
                params={"underlying": "NIFTY", "expiry": "2026-04-24", "refresh": True},
            )
            assert first.status_code == 200

            fake.call_oi = 14000
            fake.put_oi = 15000
            second = client.get(
                "/api/v1/options/chain",
                params={"underlying": "NIFTY", "expiry": "2026-04-24", "refresh": True},
            )
            assert second.status_code == 200

            heatmap = client.get(
                "/api/v1/options/oi/heatmap",
                params={"underlying": "NIFTY", "expiry": "2026-04-24", "limit": 5},
            )
            assert heatmap.status_code == 200
            rows = heatmap.json()
            assert rows
            latest = rows[0]
            assert latest["total_oi"] == 29000
            assert latest["total_oi_change"] == 7000
            assert latest["total_oi_change_pct"] > 30
    finally:
        options_chain_service.fyers_client = original_client


def test_phase3_oi_heatmap_and_spikes() -> None:
    original_client = options_chain_service.fyers_client
    options_chain_service.fyers_client = FakeFyersClientPhase3()  # type: ignore[assignment]
    try:
        with TestClient(app) as client:
            refresh = client.get(
                "/api/v1/options/chain",
                params={"underlying": "NIFTY", "expiry": "2026-04-24", "refresh": True},
            )
            assert refresh.status_code == 200

            heatmap = client.get("/api/v1/options/oi/heatmap", params={"underlying": "NIFTY", "expiry": "2026-04-24"})
            assert heatmap.status_code == 200
            rows = heatmap.json()
            assert len(rows) >= 1
            assert "total_oi" in rows[0]

            spikes = client.get(
                "/api/v1/options/oi/spikes",
                params={"underlying": "NIFTY", "expiry": "2026-04-24", "threshold_pct": 0},
            )
            assert spikes.status_code == 200
            assert len(spikes.json()) >= 1
    finally:
        options_chain_service.fyers_client = original_client
