from __future__ import annotations

import argparse
import time
from statistics import quantiles

import httpx


def main() -> None:
    parser = argparse.ArgumentParser(description="Options performance smoke test for 48 strikes")
    parser.add_argument("--base-url", default="http://localhost:8000")
    parser.add_argument("--rounds", type=int, default=10)
    parser.add_argument("--max-p95-ms", type=float, default=1500.0)
    args = parser.parse_args()

    base = args.base_url.rstrip("/")
    latencies_ms: list[float] = []
    with httpx.Client(timeout=20) as client:
        for _ in range(args.rounds):
            started = time.perf_counter()
            chain = client.get(
                f"{base}/api/v1/options/chain",
                params={"underlying": "NIFTY", "expiry": "2026-04-24", "limit": 48},
            )
            chain.raise_for_status()
            metrics = client.get(
                f"{base}/api/v1/options/metrics",
                params={"underlying": "NIFTY", "expiry": "2026-04-24"},
            )
            metrics.raise_for_status()
            latencies_ms.append((time.perf_counter() - started) * 1000)

    p95 = quantiles(latencies_ms, n=100)[94]
    avg = sum(latencies_ms) / len(latencies_ms)
    print(f"options_48 p95={p95:.2f}ms avg={avg:.2f}ms rounds={args.rounds}")
    if p95 > args.max_p95_ms:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
