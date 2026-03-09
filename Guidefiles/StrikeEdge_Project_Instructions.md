# StrikeEdge - Project Instructions

## Project Overview

**StrikeEdge** is an options screening platform that applies technical indicators directly to individual option strike price charts — not just the underlying. This is a unique capability in the Indian retail trading market.

**Core Innovation**: When Nifty spot is at 24000, the 24000 CE strike has its own OHLCV chart. StrikeEdge runs RSI, MACD, Bollinger Bands, etc. on EACH strike's candles, enabling scans like: "Show me all strikes where RSI crosses above 60."

---

## Tech Stack

### Backend
- **Language**: Python 3.12
- **Framework**: FastAPI (async, auto-docs)
- **Task Queue**: Celery + Redis
- **Data Source**: Fyers API v3 (free, already have API access)

### Databases (Local → Production)
| Local (Free) | Production (Paid) |
|--------------|-------------------|
| SQLite | Aurora Serverless v2 |
| File-based cache | ElastiCache Redis |
| ChromaDB | S3 Vectors |

### Frontend
- **Web**: React 18 + TypeScript + Tailwind CSS
- **Mobile**: React Native (Phase 6)
- **Charts**: TradingView Lightweight Charts

### Infrastructure
| Local | Production |
|-------|------------|
| uvicorn | API Gateway + Lambda |
| In-process queue | SQS |
| Local files | S3 + CloudFront |

### AI/ML (Local → Production)
| Local (Free) | Production (Paid) |
|--------------|-------------------|
| Ollama (Llama3.2, Mistral) | AWS Bedrock (Claude, Nova) |
| sentence-transformers | SageMaker Embeddings |
| nomic-embed-text | Titan Embeddings |

**No Docker Required**: All local development uses native Python and SQLite.

---

## Architecture

### Local Development (No Docker)
```
[Data Layer] → [Processing Layer] → [Application Layer]
     ↓               ↓                    ↓
Fyers API v3    Python + pandas-ta   React (Vite)
SQLite DB       Ollama (local LLM)   FastAPI
File Cache      In-process queue     uvicorn
ChromaDB        Local embeddings     localhost:8000
```

### Production Architecture
```
[Data Layer] → [Processing Layer] → [Application Layer]
     ↓               ↓                    ↓
Fyers API v3    Lambda + Bedrock     CloudFront + S3
Aurora + Redis  SQS + EventBridge    API Gateway
S3 Vectors      SageMaker            React (static)
```

### Data Flow
1. **Tick Ingestion**: Fyers WebSocket → Raw ticks
2. **Candle Building**: Redis aggregates ticks into 1m/5m/15m candles per strike
3. **Indicator Engine**: Celery workers compute RSI, MACD, etc. on each strike
4. **Signal Detection**: Compare current vs previous values for crossovers
5. **Results Push**: WebSocket broadcasts matches to subscribed users

### Scale Challenge
- ~200 F&O underlyings
- ~40 strikes × 2 (CE/PE) × 3 expiries = ~48,000 strike charts
- Update every 1-5 minutes
- Need last 50-100 candles per strike for indicator calculation

---

## Project Structure

```
strikeedge/
├── .env.example
├── docker-compose.yml          # Local dev services
├── terraform/
│   ├── 1_networking/
│   ├── 2_database/
│   ├── 3_compute/
│   ├── 4_api/
│   ├── 5_ml/
│   └── 6_monitoring/
├── backend/
│   ├── api/                    # FastAPI app
│   │   ├── main.py
│   │   ├── routers/
│   │   └── schemas/
│   ├── data_pipeline/          # Tick ingestion
│   │   ├── fyers_client.py
│   │   ├── candle_builder.py
│   │   └── instrument_sync.py
│   ├── indicators/             # Technical analysis
│   │   ├── rsi.py
│   │   ├── macd.py
│   │   ├── bollinger.py
│   │   └── engine.py
│   ├── screener/               # Scan engine
│   │   ├── scanner.py
│   │   ├── signals.py
│   │   └── filters.py
│   ├── ml/                     # AI models
│   │   ├── patterns.py
│   │   └── sentiment.py
│   └── database/               # Shared DB utilities
│       ├── models.py
│       └── schemas.py
├── frontend/
│   ├── web/                    # React web app
│   └── mobile/                 # React Native app
├── tests/
│   ├── unit/
│   ├── integration/
│   └── e2e/
└── docs/
```

---

## Development Phases

### Phase 1: Foundation & Data Pipeline (Weeks 1-4)
- Fyers API v3 integration
- Scrip master loader
- Historical candle fetcher
- Redis candle storage
- Basic indicator engine (RSI, MACD, EMA)

### Phase 2: Screener Engine & Basic UI (Weeks 5-8)
- Signal detection logic (crossovers, thresholds)
- FastAPI endpoints
- React screener builder UI
- Results table with live updates
- Strike chart viewer

### Phase 3: Options Data & Advanced Filters (Weeks 9-12)
- IV calculation, Greeks (mibian/py_vollib)
- OI change tracking, Put/Call ratio
- Combined filters (RSI + IV + OI)
- Underlying technicals correlation

### Phase 4: User System & Strategy Management (Weeks 13-16)
- Clerk auth integration
- Save/load screener configurations
- Alert system (email/push)
- Watchlists, favorites

### Phase 5: AI/ML Signals & Marketplace (Weeks 17-22)
- Pattern recognition ML model
- Sentiment analysis
- Strategy marketplace (publish/share)

### Phase 6: Mobile & Production (Weeks 23-28)
- React Native app
- AWS production deployment
- Load testing, security audit
- Beta launch

---

## Key APIs & Endpoints

### Fyers API v3
- **Instrument Master**: `https://public.fyers.in/sym_details/NSE_FO.csv`
- **Historical Candles**: `fyers.history()` - 1m to 1d intervals
- **WebSocket**: `fyers.websocket` for real-time ticks
- **Market Data**: IV, OI, Greeks

### StrikeEdge API (to build)
- `GET /api/instruments` - List all F&O instruments
- `GET /api/strikes/{underlying}` - Get strikes for underlying
- `POST /api/scan` - Run screener with parameters
- `GET /api/scan/{id}/results` - Get scan results (WebSocket for live)
- `GET /api/chart/{strike_token}` - Get OHLCV + indicators for strike
- `POST /api/strategies` - Save screener configuration
- `GET /api/alerts` - User's active alerts

---

## Coding Guidelines

### Python (Backend)
- Use `uv` for package management
- Type hints everywhere (Pydantic for validation)
- Async/await for I/O operations
- Follow FastAPI best practices
- Tests with pytest, coverage > 80%

### TypeScript (Frontend)
- Strict mode enabled
- React functional components + hooks
- Tailwind for styling (no custom CSS unless necessary)
- React Query for data fetching
- Zustand for state management

### Database
- Use Pydantic models that match DB schemas
- TimescaleDB hypertables for OHLCV
- Redis for anything < 24 hours old
- PostgreSQL for persistent user data

### Testing
- Unit tests for indicator calculations
- Integration tests for API endpoints
- E2E tests for critical user flows
- Backtest indicator accuracy against TradingView

---

## Environment Variables

```env
# Fyers API v3
FYERS_APP_ID=XXXXXX-100
FYERS_SECRET_KEY=your_secret_key
FYERS_REDIRECT_URI=https://127.0.0.1:8000/callback
FYERS_TOTP_SECRET=your_totp_secret

# Database
POSTGRES_URL=postgresql://user:pass@localhost:5432/strikeedge
REDIS_URL=redis://localhost:6379
TIMESCALE_URL=postgresql://user:pass@localhost:5433/timescale

# Auth
CLERK_SECRET_KEY=sk_test_xxx
NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY=pk_test_xxx

# AWS (Production)
AWS_REGION=ap-south-1
AWS_ACCOUNT_ID=123456789012
```

---

## Current Status

**Phase**: Pre-development (Planning Complete)
**Next Step**: Set up project repository and Docker Compose for local development

---

## Multi-Agent Architecture

StrikeEdge uses 8 specialized AI agents:

### Core Agents
| Agent | Role | Trigger |
|-------|------|---------|
| 🎯 Orchestrator | Master coordinator | User request |
| 🔬 Researcher | Market intelligence | Every 2 hours (autonomous) |
| 📊 Scanner | Execute screener scans | Orchestrator |
| 🧪 Backtester | Test strategies | Orchestrator |
| ⚡ Optimizer | Parameter tuning | Orchestrator |

### Support Agents
| Agent | Role | Trigger |
|-------|------|---------|
| 🏷️ Tagger | Classify strikes, Greeks | Orchestrator |
| 📈 Charter | Generate visualizations | Orchestrator |
| 📝 Reporter | Write analysis reports | Orchestrator |

### Workflow Examples
```
SCAN:     User → Orchestrator → Scanner → Tagger → Charter → Reporter → User
BACKTEST: User → Orchestrator → Tagger → Backtester → Charter → Reporter → User
OPTIMIZE: User → Orchestrator → Optimizer → [Backtester × N] → Reporter → User
RESEARCH: EventBridge → Researcher → S3 Vectors (autonomous, every 2 hrs)
```

### Agent Infrastructure
- **Compute**: AWS Lambda (256MB - 2048MB based on agent)
- **Queue**: SQS for job processing
- **Storage**: Aurora PostgreSQL + S3 Vectors
- **AI**: AWS Bedrock (Claude Sonnet)
- **Observability**: LangFuse tracing

---

---

## Multi-Agent System

StrikeEdge uses a sophisticated multi-agent AI architecture for research, testing, and optimization.

### Agent Orchestra

```
Orchestrator (Conductor)
    │
    ├── Specialist Agents
    │   ├── 📊 Market Researcher - Gathers market intelligence
    │   ├── 🔬 Strategy Optimizer - Optimizes parameters
    │   ├── ⚡ Backtester - Tests against historical data
    │   ├── 📈 Signal Scanner - Real-time signal detection
    │   ├── 🎯 Options Analyzer - Deep options analysis
    │   └── 🛡️ Risk Manager - Portfolio risk monitoring
    │
    └── Support Agents
        ├── 🏷️ Strike Tagger - Classifies strikes
        ├── 📰 News Sentiment - Analyzes news
        ├── 💹 Greeks Calculator - Computes Greeks
        └── 📋 Report Generator - Creates reports
```

### Key Agents

| Agent | Role | Trigger |
|-------|------|---------|
| Orchestrator | Coordinates all agents | User request / SQS |
| Market Researcher | Gathers news, FII/DII data | Every 2 hours |
| Strategy Optimizer | Parameter optimization | User request |
| Backtester | Historical testing | User request |
| Signal Scanner | Real-time screening | Continuous |
| Options Analyzer | Strike analysis | User request |
| Risk Manager | Portfolio risk | Before trades |

### Agent Infrastructure
- **Compute**: AWS Lambda (serverless)
- **Queue**: SQS for job management
- **AI Models**: AWS Bedrock (Claude Sonnet, Nova Pro)
- **Knowledge Base**: S3 Vectors
- **Observability**: LangFuse tracing

---

## When Helping Me

1. **Always consider the scale**: 48,000 strikes, real-time updates
2. **Prioritize accuracy**: Financial data must be precise (validate against TradingView)
3. **Keep it simple first**: Get one indicator working on one strike before scaling
4. **Use the tech stack defined above**: Don't suggest alternatives unless I ask
5. **Reference the phase we're in**: Focus on current phase deliverables
6. **Code should be production-ready**: Type hints, error handling, logging
7. **Follow agent patterns**: Use the multi-agent architecture for AI features
