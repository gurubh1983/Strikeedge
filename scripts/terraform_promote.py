from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path


def run_cmd(cmd: list[str], cwd: Path) -> None:
    proc = subprocess.run(cmd, cwd=str(cwd))
    if proc.returncode != 0:
        raise SystemExit(proc.returncode)


def main() -> None:
    parser = argparse.ArgumentParser(description="Terraform promotion helper for StrikeEdge environments.")
    parser.add_argument("--env", required=True, choices=["dev", "staging", "preprod", "prod"])
    parser.add_argument("--apply", action="store_true", help="Apply after plan. Default is plan-only.")
    args = parser.parse_args()

    db_password = os.getenv("TF_VAR_db_master_password")
    if not db_password:
        raise SystemExit("Missing TF_VAR_db_master_password environment variable.")

    repo_root = Path(__file__).resolve().parents[1]
    tf_dir = repo_root / "infra" / "terraform" / "environments" / args.env
    if not tf_dir.exists():
        raise SystemExit(f"Terraform environment directory not found: {tf_dir}")

    run_cmd(["terraform", "init"], cwd=tf_dir)
    run_cmd(["terraform", "plan", f"-var=db_master_password={db_password}"], cwd=tf_dir)
    if args.apply:
        run_cmd(["terraform", "apply", f"-var=db_master_password={db_password}", "-auto-approve"], cwd=tf_dir)

    print({"environment": args.env, "applied": args.apply})


if __name__ == "__main__":
    main()
