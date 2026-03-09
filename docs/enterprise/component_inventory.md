# StrikeEdge Component Inventory

## Core API
- `backend/app/main.py`: app factory, middleware, health, metrics
- `backend/app/api/routes_v1.py`: v1 API and websocket endpoints

## Data Pipeline
- `backend/app/data_pipeline/fyers_client.py`: instrument master integration and filters
- `backend/app/data_pipeline/instrument_sync.py`: NFO option sync into DB
- `backend/app/data_pipeline/tick_handler.py`: tick buffering and candle construction
- `backend/app/data_pipeline/websocket_client.py`: reconnect-capable websocket consumer
- `backend/app/data_pipeline/candle_fetcher.py`: historical candle fetch + DataFrame parser

## Indicators and Scanner
- `backend/app/domain/indicators.py`: EMA, RSI, MACD primitives
- `backend/app/indicators/rsi.py`: RSI module wrapper
- `backend/app/indicators/macd.py`: MACD line/signal/histogram module
- `backend/app/screener/scanner.py`: row-level condition screening
- `backend/app/services/screener.py`: scan execution and persisted scan jobs

## Persistence and Repositories
- `backend/app/db/models.py`: SQLAlchemy models
- `backend/app/db/session.py`: engine/session factory
- `backend/app/db/init_db.py`: DB init helper
- `backend/app/repositories/base.py`: repository protocol
- `backend/app/repositories/memory.py`: in-memory repository
- `backend/app/repositories/sqlalchemy.py`: SQLAlchemy repository

## Runtime Services
- `backend/app/services/market_data.py`: tick->candle->indicator persistence pipeline
- `backend/app/services/instruments.py`: instrument and strike query service
- `backend/app/services/strategy.py`: strategy/workspace/alert logic and validations
- `backend/app/services/scan_store.py`: scan job persistence and retrieval
- `backend/app/services/idempotency.py`: idempotency persistence layer
- `backend/app/services/realtime.py`: websocket broadcast hub
- `backend/app/services/ai.py`: AI insight service
- `backend/app/services/ollama_client.py`: Ollama generate/embed client

## Security / Observability
- `backend/app/core/auth.py`: auth provider abstraction
- `backend/app/core/security.py`: actor/idempotency/rate-limit guards
- `backend/app/core/errors.py`: error envelope handlers
- `backend/app/core/observability.py`: trace and request metrics middleware
- `backend/app/core/logging.py`: structured JSON logging helper
- `backend/app/core/metrics.py`: in-memory metrics registry

## Scripts
- `backend/scripts/apply_migrations.py`: SQL migration runner
- `backend/scripts/sync_instruments.py`: instrument sync runner
- `backend/scripts/run_ws_ingest.py`: websocket ingest runtime
- `backend/scripts/run_tick_scheduler.py`: periodic tick scheduler
- `scripts/load_test_smoke.py`: API latency smoke test
