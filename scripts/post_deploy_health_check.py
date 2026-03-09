from __future__ import annotations

import argparse
import sys
import time

import httpx


def check_endpoint(client: httpx.Client, url: str, expected_status: int = 200) -> tuple[bool, str]:
    try:
        response = client.get(url)
        ok = response.status_code == expected_status
        return ok, f"{url} -> {response.status_code}"
    except Exception as exc:
        return False, f"{url} -> error: {exc}"


def main() -> None:
    parser = argparse.ArgumentParser(description="Post-deploy health checks for StrikeEdge.")
    parser.add_argument("--base-url", default="http://localhost:8000", help="Base API URL")
    parser.add_argument("--timeout-seconds", type=float, default=10.0)
    parser.add_argument("--retries", type=int, default=3)
    args = parser.parse_args()

    endpoints = [
        ("/health", 200),
        ("/ready", 200),
        ("/metrics", 200),
        ("/metrics/prometheus", 200),
        ("/api/v1/instruments", 200),
    ]

    with httpx.Client(timeout=args.timeout_seconds) as client:
        all_ok = True
        for path, status in endpoints:
            url = f"{args.base_url.rstrip('/')}{path}"
            ok = False
            detail = ""
            for attempt in range(args.retries):
                ok, detail = check_endpoint(client, url, expected_status=status)
                if ok:
                    break
                if attempt < args.retries - 1:
                    time.sleep(1)
            print(detail)
            all_ok = all_ok and ok

    if not all_ok:
        raise SystemExit(1)
    print("post_deploy_health_check: ok")


if __name__ == "__main__":
    main()
