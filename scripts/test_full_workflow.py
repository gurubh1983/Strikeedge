from __future__ import annotations

import argparse
import uuid

import httpx


def main() -> None:
    parser = argparse.ArgumentParser(description="Full StrikeEdge scanner workflow validation")
    parser.add_argument("--base-url", default="http://localhost:8000")
    args = parser.parse_args()

    base = args.base_url.rstrip("/")
    headers = {"x-actor-id": "workflow-tester", "x-idempotency-key": str(uuid.uuid4())}

    with httpx.Client(timeout=15) as client:
        health = client.get(f"{base}/health")
        ready = client.get(f"{base}/ready")
        assert health.status_code == 200
        assert ready.status_code == 200

        instruments = client.get(f"{base}/api/v1/instruments")
        assert instruments.status_code == 200
        assert isinstance(instruments.json(), list)

        create_screener = client.post(
            f"{base}/api/v1/screeners",
            json={
                "user_id": "workflow-user",
                "name": "Workflow Screener",
                "timeframe": "5m",
                "groups": [{"logical_operator": "AND", "rules": [{"field": "rsi_14", "operator": ">", "value": 50}]}]
            },
            headers=headers,
        )
        assert create_screener.status_code == 200
        screener_id = create_screener.json()["id"]

        scan = client.post(
            f"{base}/api/v1/scan",
            json={
                "timeframe": "5m",
                "groups": [{"logical_operator": "OR", "rules": [{"field": "ema_20", "operator": ">", "value": 90}]}],
            },
        )
        assert scan.status_code == 200
        scan_id = scan.json()["scan_id"]

        results = client.get(f"{base}/api/v1/scan/{scan_id}/results")
        assert results.status_code == 200
        assert isinstance(results.json().get("results", []), list)

        options_chain = client.get(
            f"{base}/api/v1/options/chain",
            params={"underlying": "NIFTY", "expiry": "2026-04-24", "refresh": True, "limit": 48},
        )
        assert options_chain.status_code == 200
        chain_rows = options_chain.json()
        assert isinstance(chain_rows, list)

        options_metrics = client.get(
            f"{base}/api/v1/options/metrics",
            params={"underlying": "NIFTY", "expiry": "2026-04-24"},
        )
        assert options_metrics.status_code == 200

        options_greeks_batch = client.post(
            f"{base}/api/v1/options/greeks/calculate",
            params={
                "underlying": "NIFTY",
                "expiry": "2026-04-24",
                "spot": 24000,
                "time_to_expiry_years": 20 / 365,
            },
        )
        assert options_greeks_batch.status_code == 200

        if chain_rows:
            first_symbol = chain_rows[0].get("call_symbol") or chain_rows[0].get("put_symbol")
            if isinstance(first_symbol, str) and first_symbol:
                options_strike_greeks = client.get(f"{base}/api/v1/strikes/{first_symbol}/vol/greeks")
                assert options_strike_greeks.status_code in {200, 404}

        oi_heatmap = client.get(
            f"{base}/api/v1/options/oi/heatmap",
            params={"underlying": "NIFTY", "expiry": "2026-04-24", "limit": 100},
        )
        assert oi_heatmap.status_code == 200

        delete_screener = client.delete(f"{base}/api/v1/screeners/{screener_id}")
        assert delete_screener.status_code == 200

    print({"workflow": "ok", "scan_id": scan_id})


if __name__ == "__main__":
    main()
