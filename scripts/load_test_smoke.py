from __future__ import annotations

import asyncio
import argparse
import time
from statistics import quantiles

import httpx


async def main(base_url: str, requests: int, max_p95_ms: float | None) -> None:
    url = f"{base_url.rstrip('/')}/api/v1/scan"
    payload = {"timeframe": "5m", "rules": [{"field": "rsi_14", "operator": ">", "value": 40}]}
    latencies = []
    async with httpx.AsyncClient(timeout=10) as client:
        for _ in range(requests):
            started = time.perf_counter()
            response = await client.post(url, json=payload)
            response.raise_for_status()
            latencies.append((time.perf_counter() - started) * 1000)
    p95 = quantiles(latencies, n=100)[94]
    avg = sum(latencies) / len(latencies)
    print(f"p95={p95:.2f}ms avg={avg:.2f}ms")
    if max_p95_ms is not None and p95 > max_p95_ms:
        raise SystemExit(1)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="StrikeEdge API smoke load checker")
    parser.add_argument("--base-url", default="http://localhost:8000")
    parser.add_argument("--requests", type=int, default=25)
    parser.add_argument("--max-p95-ms", type=float, default=None)
    args = parser.parse_args()
    asyncio.run(main(base_url=args.base_url, requests=args.requests, max_p95_ms=args.max_p95_ms))
