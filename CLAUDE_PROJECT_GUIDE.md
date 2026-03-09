# StrikeEdge – Claude Project Guide

**Purpose:** Use this guide when testing the entire project, updating dependencies, or identifying and completing pending work.

---

## Project Structure

```
StrikeEdge/
├── backend/                 # Python FastAPI backend
│   ├── app/                 # Application code
│   │   ├── agents/          # Multi-agent system (Orchestrator, Tagger, Greeks, Scanner, etc.)
│   │   ├── api/             # REST routes
│   │   ├── core/            # Settings, errors, metrics, observability
│   │   ├── db/              # Models, session
│   │   ├── services/        # Business logic (market_data, options_volatility, agent_runner, etc.)
│   │   ├── screener/        # Scanner, conditions
│   │   └── data_pipeline/   # Candle fetcher, tick handler
│   ├── tests/               # pytest test suite
│   ├── migrations/          # SQL migrations
│   └── pyproject.toml       # Python dependencies
├── frontend/web/            # Next.js frontend
│   └── package.json         # Node/npm dependencies
├── Guidefiles/              # Architecture & phase docs
│   ├── StrikeEdge_Agent_Architecture.md
│   └── Phase5_Signoff.md
├── .env                     # Environment variables (DO NOT COMMIT)
└── CLAUDE_PROJECT_GUIDE.md  # This file
```

---

## Testing the Entire Project

### Backend (Python)

**Prerequisites:** Python 3.12+, pip or uv

```bash
cd backend
pip install -e ".[research]"   # Install with optional research (chromadb)
# Or: pip install -e .
```

**Run all tests:**
```bash
cd backend
python -m pytest -v
```

**Run specific test groups:**
```bash
# Agent & workflow tests
python -m pytest tests/test_agents.py -v

# Options chain, OI, Greeks
python -m pytest tests/test_phase3_options_oi_and_greeks.py tests/test_options_analytics.py -v

# Market data, candles, tick handler
python -m pytest tests/test_market_data_pipeline.py tests/test_strike_candles_api.py tests/test_tick_handler.py -v

# Screener, indicators
python -m pytest tests/test_candle_fetcher_and_scanner.py tests/test_indicators.py -v

# Auth, metrics, notifications
python -m pytest tests/test_auth_and_metrics.py tests/test_notifications.py -v

# Full suite with coverage
python -m pytest --cov=app -v
```

**PowerShell (Windows):**
```powershell
cd backend; python -m pytest -v
```

### Frontend (Next.js)

**Prerequisites:** Node 18+, npm or yarn

```bash
cd frontend/web
npm install
npm run build
npm run lint
```

**Start dev server:**
```bash
npm run dev
```

---

## Dependencies

### Backend (`backend/pyproject.toml`)

| Package        | Purpose                    | Update command              |
|----------------|----------------------------|-----------------------------|
| fastapi        | API framework              | `pip install -U fastapi`    |
| uvicorn        | ASGI server                | `pip install -U uvicorn`    |
| sqlalchemy     | ORM                        | `pip install -U sqlalchemy` |
| httpx          | HTTP client                | `pip install -U httpx`      |
| pandas         | Data handling              | `pip install -U pandas`     |
| beautifulsoup4 | Web scraping (Sentiment)   | `pip install -U beautifulsoup4` |
| apscheduler    | Job scheduling             | `pip install -U apscheduler`|
| chromadb       | Optional, research storage | `pip install chromadb`      |

**Update all backend deps:**
```bash
cd backend
pip install -U -e .
# Or with uv: uv pip install -e . --upgrade
```

**Check for outdated packages:**
```bash
pip list --outdated
```

### Frontend (`frontend/web/package.json`)

**Update all frontend deps:**
```bash
cd frontend/web
npm update
# Or: npm outdated  # then npm install <pkg>@latest
```

---

## Environment Configuration

**Key variables** (see `.env`; copy from `.env.example` if present):

| Variable               | Required | Purpose                          |
|------------------------|----------|----------------------------------|
| STRIKEEDGE_DATABASE_URL| Yes      | SQLite or PostgreSQL URL         |
| STRIKEEDGE_ENVIRONMENT | No       | dev / staging / prod             |
| OPENAI_API_KEY         | Optional | AI sentiment, embeddings          |
| NEWS_API_KEY           | Optional | Researcher news fetching         |
| FYERS_*                | Optional | Fyers broker integration         |

**Backend startup checks:** `app/core/startup_checks.py` validates runtime settings.

---

## Pending Work & Known Gaps

Use this list when asked to "update dependencies" or "complete pending work."

### Backend
- [ ] **ChromaDB** – Optional; install with `pip install strikeedge-backend[research]` for research storage
- [ ] **News API** – Set `NEWS_API_KEY` in `.env` for Researcher news fetching
- [ ] **Fyers** – Configure FYERS_* for live market data; tests may use in-memory fallbacks
- [ ] **Database** – Default SQLite; for production, switch to PostgreSQL/TimescaleDB per `.env`

### Frontend
- [ ] Verify Clerk auth env vars (`NEXT_PUBLIC_CLERK_*`) if using auth
- [ ] Run `npm audit fix` periodically for security updates

### Integration
- [ ] End-to-end tests (backend + frontend) – not yet defined
- [ ] Load / stress testing for agent workflows

### Reference Docs
- **Architecture:** `Guidefiles/StrikeEdge_Agent_Architecture.md`
- **Phase 5 completion:** `Guidefiles/Phase5_Signoff.md`

---

## Quick Commands Reference

| Action              | Command                                       |
|---------------------|-----------------------------------------------|
| Backend tests       | `cd backend && python -m pytest -v`          |
| Backend run         | `cd backend && uvicorn app.main:app --reload` |
| Frontend install    | `cd frontend/web && npm install`             |
| Frontend dev        | `cd frontend/web && npm run dev`             |
| Frontend build      | `cd frontend/web && npm run build`           |
| Frontend lint       | `cd frontend/web && npm run lint`            |
| Migrations          | `cd backend && alembic upgrade head`          |

---

## Troubleshooting

1. **Tests fail with DB errors:** Ensure `STRIKEEDGE_DATABASE_URL` points to a valid DB. Tests use in-memory fallbacks where possible.
2. **Import errors:** Run `pip install -e .` from `backend/` to install the app in editable mode.
3. **Agent jobs 404:** Agent runner uses in-memory jobs when `session_factory` is unset (e.g. in tests).
4. **NSE FII/DII fails:** NSE may block requests; Researcher falls back gracefully.
5. **ChromaDB errors:** Optional; install with `pip install chromadb` or ignore if not needed.
6. **Dashboard shows +0.00% and "Restart backend for live data":** The `/api/v1/dashboard/market-overview` route returns 404. Known issue: multiple backend processes can bind to port 8000 on Windows; older processes may not have the dashboard route. Workaround: fully stop all backends (Ctrl+C in every terminal), kill processes on port 8000 (`Get-NetTCPConnection -LocalPort 8000 | ForEach-Object { Stop-Process -Id $_.OwningProcess -Force }`), wait a few seconds, then run `backend/restart.ps1`. Verify: http://localhost:8000/api/v1/dashboard/market-overview should return JSON, not 404. See `backend/RESTART_INSTRUCTIONS.md`.

---

## Checklist for Full Project Test Run

When asked to "test the entire project":

1. **Backend:** `cd backend && python -m pytest -v` → all tests pass
2. **Frontend:** `cd frontend/web && npm run build` → build succeeds
3. **Frontend lint:** `npm run lint` → no errors
4. **Backend server:** `uvicorn app.main:app --reload` → server starts, `/health` returns 200
5. **Dependencies:** Run `pip list --outdated` and `npm outdated`; suggest updates if safe

When asked to "update dependencies":

1. Bump versions in `pyproject.toml` and `package.json` where appropriate
2. Run `pip install -e .` and `npm install` to apply
3. Re-run tests to confirm no regressions

---

*Last updated: March 2026*

---

## Known Issues

| Issue | Symptom | Workaround |
|-------|---------|------------|
| Dashboard 404 | Momentum Dashboard shows "+0.00%" everywhere, "Restart backend for live data" | Kill all processes on port 8000, restart backend with `backend/restart.ps1`. See `backend/RESTART_INSTRUCTIONS.md`. |
