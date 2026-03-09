# Phase 0 Hardening Checklist

## Backend Baseline
- [x] App factory and modular router structure
- [x] Settings management via environment-driven config
- [x] SQLAlchemy persistence foundation with startup initialization
- [x] Repository abstraction (memory and SQLAlchemy implementations)
- [x] Auth provider abstraction for future Clerk/JWT integration
- [x] Observability middleware with trace ID and elapsed timing headers

## Delivery Safety
- [x] Mutation endpoint guards (actor identity + idempotency key)
- [x] Unit/integration tests for core API paths
- [x] CI test workflow in GitHub Actions

## Next (Phase 0.2)
- [x] Replace stub auth provider with JWT/Clerk verification
- [x] Add migrations (Alembic) for schema versioning
- [x] Add typed DTOs for persistence read models
- [x] Introduce service-level structured logging + metrics export
