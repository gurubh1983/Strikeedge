from __future__ import annotations

from unittest.mock import patch

from fastapi.testclient import TestClient

from app.main import app
from app.services.options_chain import options_chain_service


class FakeFyersClient:
    async def fetch_scrip_master(self) -> list[dict]:
        return [
            {
                "exch_seg": "NFO",
                "instrumenttype": "OPTIDX",
                "symbol": "NIFTY24APR24000CE",
                "name": "NIFTY",
                "expiry": "2026-04-24",
                "strike": "2400000",
                "token": "111",
                "lotsize": 50,
            },
            {
                "exch_seg": "NFO",
                "instrumenttype": "OPTIDX",
                "symbol": "NIFTY24APR24000PE",
                "name": "NIFTY",
                "expiry": "2026-04-24",
                "strike": "2400000",
                "token": "112",
                "lotsize": 50,
            },
        ]

    @staticmethod
    def filter_nfo_options(records: list[dict]) -> list[dict]:
        from app.data_pipeline.fyers_client import FyersClient

        return FyersClient.filter_nfo_options(records)

    @staticmethod
    def filter_by_expiry(records: list[dict], expiry: str) -> list[dict]:
        from app.data_pipeline.fyers_client import FyersClient

        return FyersClient.filter_by_expiry(records, expiry)

    @staticmethod
    def build_options_chain(records: list[dict], *, underlying: str, expiry: str) -> list[dict]:
        from app.data_pipeline.fyers_client import FyersClient

        return FyersClient.build_options_chain(records, underlying=underlying, expiry=expiry)


def test_options_chain_refresh_and_get() -> None:
    original_client = options_chain_service.fyers_client
    options_chain_service.fyers_client = FakeFyersClient()  # type: ignore[assignment]
    try:
        with patch("app.services.fyers_token_store.load_token", return_value=None):
            with TestClient(app) as client:
                refresh_resp = client.get(
                    "/api/v1/options/chain",
                    params={"underlying": "NIFTY", "expiry": "2026-04-24", "refresh": True},
                )
                assert refresh_resp.status_code == 200
                rows = refresh_resp.json()
                assert len(rows) >= 1
                assert rows[0]["underlying"] == "NIFTY"
                assert isinstance(rows[0]["strike_price"], (int, float))
                assert rows[0]["strike_price"] > 0

                get_resp = client.get("/api/v1/options/chain", params={"underlying": "NIFTY", "expiry": "2026-04-24"})
                assert get_resp.status_code == 200
                assert len(get_resp.json()) >= 1

                metrics_resp = client.get("/api/v1/options/metrics", params={"underlying": "NIFTY", "expiry": "2026-04-24"})
                assert metrics_resp.status_code == 200
                metrics = metrics_resp.json()
                assert metrics["underlying"] == "NIFTY"
                assert metrics["strikes"] >= 1

                greeks_resp = client.get(
                    "/api/v1/options/greeks",
                    params={
                        "option_type": "CE",
                        "spot": 24000,
                        "strike": 24000,
                        "time_to_expiry_years": 0.05,
                        "risk_free_rate": 0.06,
                        "volatility": 0.2,
                    },
                )
                assert greeks_resp.status_code == 200
                greeks = greeks_resp.json()
                assert "delta" in greeks
    finally:
        options_chain_service.fyers_client = original_client
