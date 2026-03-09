# StrikeEdge Monorepo (Phase 0)

This repository is organized as a monorepo baseline for enterprise rollout:

- `backend/` FastAPI services and domain modules
- `frontend/` Next.js/React UI modules
- `docs/` architecture, UI, ops, and security references
- `infra/terraform/` infrastructure scaffolding
- `.github/workflows/` CI gates

## Quick Start

- Run backend tests: `python -m pytest backend/tests -q`
- Run API locally: `uvicorn app.main:app --reload` (from `backend/`)
- Apply SQL migrations (SQLite): `python scripts/apply_migrations.py` (from `backend/`)
- Alembic migration status: `alembic -c alembic.ini current` (from `backend/`)
- Alembic autogenerate revision: `alembic -c alembic.ini revision --autogenerate -m "message"` (from `backend/`)
- Frontend dev server: `npm install && npm run dev` (from `frontend/web/`)
- Frontend lint: `npm run lint` (from `frontend/web/`)
- Options full-flow validation: `python scripts/test_options_full_flow.py --base-url http://localhost:8000`
- Options 48-strike performance smoke: `python scripts/performance_test_options_48.py --base-url http://localhost:8000 --rounds 10 --max-p95-ms 1500`
- Strike greeks batch job: `python backend/scripts/run_strike_greeks_batch.py --underlying NIFTY --expiry 2026-04-24 --spot 24000 --time-to-expiry-years 0.0548`
- Notification outbox dispatcher: `python scripts/run_notification_dispatcher.py --limit 100` (from `backend/`)
