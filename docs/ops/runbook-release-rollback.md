# Release Rollback Runbook

Use this runbook when a release must be rolled back after deployment.

## Preconditions

1. Confirm severity and scope (API errors, data integrity, latency regression).
2. Freeze further rollout and notify stakeholders.
3. Ensure latest DB snapshot exists before rollback actions.

## Commands

### 1) Verify current service health

- `python scripts/post_deploy_health_check.py --base-url http://localhost:8000`

### 2) Snapshot Aurora before rollback

- Dry run:
  - `python scripts/aws_db_snapshot.py --cluster-id strikeedge-prod-aurora create`
- Execute:
  - `python scripts/aws_db_snapshot.py --cluster-id strikeedge-prod-aurora create --execute`

### 3) Roll infra/app back to previous known-good revision

- Terraform plan for target environment:
  - `python scripts/terraform_promote.py --env prod`
- Apply after verification:
  - `python scripts/terraform_promote.py --env prod --apply`

### 4) Validate post-rollback

1. `python scripts/post_deploy_health_check.py --base-url <prod-api-url>`
2. Run smoke scan check:
   - `python scripts/load_test_smoke.py`
3. Confirm error budgets and alerts return to normal.

## Database restore (if required)

If data rollback is required, restore from the selected snapshot:

- Dry run restore command:
  - `python scripts/aws_db_snapshot.py --cluster-id strikeedge-prod-aurora restore --snapshot-id <snapshot-id> --target-cluster-id strikeedge-prod-aurora-rollback --subnet-group strikeedge-prod-db-subnets --security-group-id <sg-id>`

Add the `--execute` flag only after change approval.
