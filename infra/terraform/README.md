# StrikeEdge Terraform Scaffolding

This Terraform stack provides production-oriented baseline resources:

- `modules/networking`: VPC + private subnets
- `modules/database`: Aurora PostgreSQL + ElastiCache Redis subnet/security setup
- `modules/compute`: ECS cluster + API log group + runtime security group
- `environments/dev`: composed deployment of networking/database/compute modules
- `environments/staging`: promotion validation environment
- `environments/preprod`: production-like certification environment
- `environments/prod`: production deployment environment

## Environment Apply

From `infra/terraform/environments/<env>` where `<env>` is `dev`, `staging`, `preprod`, or `prod`:

1. `terraform init`
2. `terraform plan -var="db_master_password=<secure-value>"`
3. `terraform apply -var="db_master_password=<secure-value>"`

Outputs include VPC ID, Aurora endpoint, Redis endpoint, and ECS cluster name.

## Optional Promotion Helper

Use the wrapper script from repo root:

- `python scripts/terraform_promote.py --env preprod`
- `python scripts/terraform_promote.py --env preprod --apply`
