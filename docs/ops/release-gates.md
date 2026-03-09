# Release Gates

1. Unit/integration tests green.
2. Security and dependency checks pass.
3. Performance smoke test meets baseline.
4. No unresolved critical defects.
5. Rollback plan validated.
6. Post-deploy health checks pass.

## Promotion Commands

Promotion sequence: `dev -> staging -> preprod -> prod`.

- Export DB password once:
  - PowerShell: `$env:TF_VAR_db_master_password="<secure-value>"`
- Plan-only promotion check:
  - `python scripts/terraform_promote.py --env dev`
  - `python scripts/terraform_promote.py --env staging`
  - `python scripts/terraform_promote.py --env preprod`
  - `python scripts/terraform_promote.py --env prod`
- Apply (operator controlled):
  - `python scripts/terraform_promote.py --env <env> --apply`

## Single-Command Orchestration

- Plan-only dry run with checks:
  - `python scripts/release_orchestrator.py --env staging --base-url <api-url> --run-full-workflow`
- Apply + checks:
  - `python scripts/release_orchestrator.py --env preprod --base-url <api-url> --apply --run-full-workflow`
- Apply without post-deploy checks (not recommended):
  - `python scripts/release_orchestrator.py --env prod --apply --skip-post-deploy`

## Post-Deploy Validation

- `python scripts/post_deploy_health_check.py --base-url <api-url>`
- `python scripts/test_full_workflow.py --base-url <api-url>`
- `python scripts/performance_test.py --base-url <api-url> --requests 100 --max-p95-ms 1200`
- readiness endpoint should return `{"status":"ready"}` for healthy deployments
- GitHub Actions manual workflow:
  - `post-deploy-health` with inputs:
    - `environment` (`dev|staging|preprod|prod`)
    - `base_url` (API base URL)

## Rollback Readiness

- Snapshot helper:
  - `python scripts/aws_db_snapshot.py --cluster-id <aurora-cluster-id> list`
  - `python scripts/aws_db_snapshot.py --cluster-id <aurora-cluster-id> create`
- Detailed rollback runbook:
  - `docs/ops/runbook-release-rollback.md`
