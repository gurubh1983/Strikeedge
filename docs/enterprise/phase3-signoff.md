# Phase 3 Sign-off (Options Intelligence)

## Scope Delivered

- Options analytics backend:
  - Black-Scholes Greeks endpoint (`GET /api/v1/options/greeks`)
  - Batch Greeks calculation (`POST /api/v1/options/greeks/calculate`)
  - Persisted strike Greeks (`strike_greeks`) and symbol lookup endpoint (`GET /api/v1/strikes/{symbol}/vol/greeks`)
- Open interest tracking:
  - OI history persistence (`oi_history`) on options chain upsert
  - OI heatmap and spike endpoints (`/api/v1/options/oi/heatmap`, `/api/v1/options/oi/spikes`)
- Option screener filters:
  - Added `delta`, `gamma`, `oi_change_pct`, `volume`, `moneyness`, `expiry_days`
- Frontend options UI:
  - options chain table with Greeks and OI color coding
  - option filter controls
  - OI heatmap view
  - strike chart on symbol click
- Integration/performance tooling:
  - options flow included in `scripts/test_full_workflow.py`
  - 48-strike performance smoke runner in `scripts/performance_test_options_48.py`

## Validation

- Backend test suite passes.
- Frontend lint passes.
- End-to-end and performance scripts are ready for operator execution against target environments.

## External Execution Items

- Run the full workflow script against real deployed environments.
- Run the 48-strike performance script and compare p95 to environment SLO.
- Complete operator sign-off in staging/preprod/prod.
