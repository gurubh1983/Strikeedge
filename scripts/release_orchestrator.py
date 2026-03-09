from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


def run_cmd(cmd: list[str], cwd: Path) -> None:
    print(" ".join(cmd))
    proc = subprocess.run(cmd, cwd=str(cwd))
    if proc.returncode != 0:
        raise SystemExit(proc.returncode)


def main() -> None:
    parser = argparse.ArgumentParser(description="Release orchestration helper for StrikeEdge.")
    parser.add_argument("--env", required=True, choices=["dev", "staging", "preprod", "prod"])
    parser.add_argument("--base-url", default=None, help="API URL for post-deploy checks.")
    parser.add_argument("--apply", action="store_true", help="Apply terraform changes.")
    parser.add_argument("--skip-tests", action="store_true", help="Skip backend test execution.")
    parser.add_argument("--skip-post-deploy", action="store_true", help="Skip post-deploy health and smoke checks.")
    parser.add_argument("--run-full-workflow", action="store_true", help="Run full API workflow validation script.")
    parser.add_argument("--run-options-flow", action="store_true", help="Run options full-flow validation script.")
    parser.add_argument("--run-options-perf48", action="store_true", help="Run options 48-strike performance smoke script.")
    args = parser.parse_args()

    repo_root = Path(__file__).resolve().parents[1]

    if not args.skip_tests:
        run_cmd([sys.executable, "-m", "pytest", "tests", "-q"], cwd=repo_root / "backend")

    promote_cmd = [sys.executable, "scripts/terraform_promote.py", "--env", args.env]
    if args.apply:
        promote_cmd.append("--apply")
    run_cmd(promote_cmd, cwd=repo_root)

    if not args.skip_post_deploy:
        if not args.base_url:
            raise SystemExit("--base-url is required unless --skip-post-deploy is set")
        run_cmd(
            [sys.executable, "scripts/post_deploy_health_check.py", "--base-url", args.base_url],
            cwd=repo_root,
        )
        if args.run_full_workflow:
            run_cmd(
                [sys.executable, "scripts/test_full_workflow.py", "--base-url", args.base_url],
                cwd=repo_root,
            )
        if args.run_options_flow:
            run_cmd(
                [sys.executable, "scripts/test_options_full_flow.py", "--base-url", args.base_url],
                cwd=repo_root,
            )
        run_cmd(
            [sys.executable, "scripts/performance_test.py", "--base-url", args.base_url, "--requests", "100", "--max-p95-ms", "1200"],
            cwd=repo_root,
        )
        if args.run_options_perf48:
            run_cmd(
                [sys.executable, "scripts/performance_test_options_48.py", "--base-url", args.base_url, "--rounds", "10", "--max-p95-ms", "1500"],
                cwd=repo_root,
            )

    print({"environment": args.env, "applied": args.apply, "post_deploy_checks": not args.skip_post_deploy})


if __name__ == "__main__":
    main()
