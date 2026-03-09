from __future__ import annotations

import argparse

import httpx


def main() -> None:
    parser = argparse.ArgumentParser(description="Options full-flow validation")
    parser.add_argument("--base-url", default="http://localhost:8000")
    parser.add_argument("--underlying", default="NIFTY")
    parser.add_argument("--expiry", default="2026-04-24")
    args = parser.parse_args()

    base = args.base_url.rstrip("/")
    with httpx.Client(timeout=20) as client:
        chain = client.get(
            f"{base}/api/v1/options/chain",
            params={"underlying": args.underlying, "expiry": args.expiry, "refresh": True, "limit": 48},
        )
        chain.raise_for_status()
        rows = chain.json()
        assert isinstance(rows, list)

        metrics = client.get(
            f"{base}/api/v1/options/metrics",
            params={"underlying": args.underlying, "expiry": args.expiry},
        )
        metrics.raise_for_status()

        batch = client.post(
            f"{base}/api/v1/options/greeks/calculate",
            params={
                "underlying": args.underlying,
                "expiry": args.expiry,
                "spot": 24000,
                "time_to_expiry_years": 20 / 365,
            },
        )
        batch.raise_for_status()

        heatmap = client.get(
            f"{base}/api/v1/options/oi/heatmap",
            params={"underlying": args.underlying, "expiry": args.expiry, "limit": 100},
        )
        heatmap.raise_for_status()

        spikes = client.get(
            f"{base}/api/v1/options/oi/spikes",
            params={"underlying": args.underlying, "expiry": args.expiry, "threshold_pct": 0},
        )
        spikes.raise_for_status()

        if rows:
            symbol = rows[0].get("call_symbol") or rows[0].get("put_symbol")
            if isinstance(symbol, str) and symbol:
                symbol_resp = client.get(f"{base}/api/v1/strikes/{symbol}/vol/greeks")
                assert symbol_resp.status_code in {200, 404}

    print({"options_flow": "ok", "underlying": args.underlying, "expiry": args.expiry})


if __name__ == "__main__":
    main()
