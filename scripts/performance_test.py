from __future__ import annotations

import argparse
import subprocess
import sys


def main() -> None:
    parser = argparse.ArgumentParser(description="Performance test runner with SLO threshold")
    parser.add_argument("--base-url", default="http://localhost:8000")
    parser.add_argument("--requests", type=int, default=100)
    parser.add_argument("--max-p95-ms", type=float, default=1200.0)
    args = parser.parse_args()

    cmd = [
        sys.executable,
        "scripts/load_test_smoke.py",
        "--base-url",
        args.base_url,
        "--requests",
        str(args.requests),
        "--max-p95-ms",
        str(args.max_p95_ms),
    ]
    result = subprocess.run(cmd, check=False)
    if result.returncode != 0:
        raise SystemExit(result.returncode)
    print({"performance": "ok", "max_p95_ms": args.max_p95_ms})


if __name__ == "__main__":
    main()
