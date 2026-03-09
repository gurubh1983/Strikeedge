from __future__ import annotations

import argparse
import datetime as dt
import subprocess
from typing import Sequence


def run(cmd: Sequence[str], execute: bool) -> None:
    rendered = " ".join(cmd)
    print(rendered)
    if execute:
        subprocess.run(cmd, check=True)


def main() -> None:
    parser = argparse.ArgumentParser(description="Aurora snapshot helper for release rollback readiness.")
    parser.add_argument("--cluster-id", required=True, help="Aurora cluster identifier")
    parser.add_argument("--region", default="ap-south-1")
    parser.add_argument("--execute", action="store_true", help="Execute commands. Default is dry-run print.")

    action = parser.add_subparsers(dest="action", required=True)
    action.add_parser("list", help="List DB cluster snapshots")

    create = action.add_parser("create", help="Create a manual DB cluster snapshot")
    create.add_argument("--snapshot-id", default=None)

    restore = action.add_parser("restore", help="Print restore command for a snapshot")
    restore.add_argument("--snapshot-id", required=True)
    restore.add_argument("--target-cluster-id", required=True)
    restore.add_argument("--subnet-group", required=True)
    restore.add_argument("--security-group-id", required=True)

    args = parser.parse_args()

    if args.action == "list":
        run(
            [
                "aws",
                "rds",
                "describe-db-cluster-snapshots",
                "--db-cluster-identifier",
                args.cluster_id,
                "--region",
                args.region,
            ],
            execute=args.execute,
        )
        return

    if args.action == "create":
        snapshot_id = args.snapshot_id or f"{args.cluster_id}-manual-{dt.datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
        run(
            [
                "aws",
                "rds",
                "create-db-cluster-snapshot",
                "--db-cluster-identifier",
                args.cluster_id,
                "--db-cluster-snapshot-identifier",
                snapshot_id,
                "--region",
                args.region,
            ],
            execute=args.execute,
        )
        return

    run(
        [
            "aws",
            "rds",
            "restore-db-cluster-from-snapshot",
            "--db-cluster-identifier",
            args.target_cluster_id,
            "--snapshot-identifier",
            args.snapshot_id,
            "--engine",
            "aurora-postgresql",
            "--db-subnet-group-name",
            args.subnet_group,
            "--vpc-security-group-ids",
            args.security_group_id,
            "--region",
            args.region,
        ],
        execute=args.execute,
    )


if __name__ == "__main__":
    main()
