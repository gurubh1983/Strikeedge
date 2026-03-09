# StrikeEdge Development Guide for Cursor/Claude Code

## Project Overview

StrikeEdge is an Indian options screener that applies **technical indicators directly to option strike price charts** (not just the underlying). This is a unique differentiator - most platforms only apply technicals to the underlying index/stock.

## Current Status (As of Session End)

### ✅ Working:
- Fyers API authentication (OAuth flow complete, token saved)
- Real-time spot prices for NIFTY and BANKNIFTY
- Options chain fetching from Fyers API
- 124 instruments loaded (62 NIFTY + 62 BANKNIFTY options)
- Options Chain Workbench displaying real data with Greeks
- Backend: FastAPI on port 8000
- Frontend: Next.js on port 3000
- Database: SQLite with instruments, candles, strike_candles tables

### ❌ Not Working / Missing:
- LTP not visible in options chain display
- No dropdown selectors for underlying/expiry
- Stock options not loaded (only index options)
- Strike-level technical scanning not implemented
- Scanner shows limited results

## Core Architecture

```
C:\Users\USER\StrikeEdge\
├── backend/
│   ├── app/
│   │   ├── api/routes_v1.py          # All API endpoints
│   │   ├── core/settings.py          # Configuration with Fyers credentials
│   │   ├── data_pipeline/fyers_auth.py  # OAuth authentication
│   │   ├── db/
│   │   │   ├── models.py             # SQLAlchemy models
│   │   │   └── session.py            # Database session factory
│   │   ├── services/
│   │   │   ├── fyers_data.py         # Fyers API: quotes, options chain, history
│   │   │   ├── fyers_token_store.py  # Token persistence (~/.strikeedge/fyers_token.json)
│   │   │   ├── market_data.py        # Market data service
│   │   │   └── options_chain.py      # Options chain processing
│   │   └── main.py                   # FastAPI app with /callback endpoint
│   └── strikeedge.db                 # SQLite database
├── frontend/web/
│   ├── src/
│   │   ├── app/                      # Next.js app router pages
│   │   └── features/options/         # Options workbench components
│   └── .env.local                    # Frontend env (Clerk keys needed)
└── .env                              # Backend environment variables
```

## Key Files to Understand

### 1. Fyers Data Service (`backend/app/services/fyers_data.py`)
```python
# Functions available:
get_quotes(symbols: list[str]) -> dict        # Live quotes for any symbol
get_spot_price(underlying: str) -> float      # NIFTY/BANKNIFTY spot
get_option_chain(underlying, expiry, strikecount) -> list  # Options chain with OI, LTP
get_history(symbol, resolution, from_date, to_date) -> list  # OHLCV candles
```

### 2. Database Models (`backend/app/db/models.py`)
```python
InstrumentModel    # Options/stocks master data
CandleModel        # Underlying candles
StrikeCandleModel  # Option strike candles (for technical analysis)
OptionsChainModel  # Options chain snapshots
```

### 3. Settings (`backend/app/core/settings.py`)
```python
# Fyers credentials accessed via:
settings = get_settings()
settings.fyers_app_id_resolved      # App ID
settings.fyers_secret_key_resolved  # Secret
settings.fyers_redirect_uri_resolved # Callback URL
```

## Priority Tasks

### Phase 1: Fix Immediate UI Issues

#### Task 1.1: Add LTP to Options Chain Display
**File:** `backend/app/api/routes_v1.py` (find options chain endpoint)
**File:** `frontend/web/src/features/options/OptionsWorkbench.tsx`

The options chain API returns LTP but frontend may not be displaying it. Check:
1. API response includes `ltp` field
2. Frontend table renders `ltp` column

#### Task 1.2: Add Dropdown Selectors
**File:** `frontend/web/src/features/options/OptionsWorkbench.tsx`

Replace text inputs with dropdowns for:
- Underlying: NIFTY, BANKNIFTY, FINNIFTY, + F&O stocks
- Expiry: Fetch from Fyers API (dynamic list)

#### Task 1.3: Fetch Available Expiries
**File:** `backend/app/services/fyers_data.py`

Add function:
```python
def get_expiries(underlying: str) -> list[dict]:
    """Return list of available expiry dates for an underlying."""
    fm = _get_fyers_model()
    symbol_map = {"NIFTY": "NSE:NIFTY50-INDEX", "BANKNIFTY": "NSE:NIFTYBANK-INDEX"}
    sym = symbol_map.get(underlying.upper(), f"NSE:{underlying.upper()}")
    resp = fm.optionchain(data={"symbol": sym, "strikecount": 1})
    return resp.get("data", {}).get("expiryData", [])
```

### Phase 2: Load Stock Options

#### Task 2.1: Get F&O Stock List
NSE F&O stocks (~180): RELIANCE, TCS, INFY, HDFCBANK, ICICIBANK, etc.

**File:** Create `backend/app/data/fo_stocks.py`
```python
FO_STOCKS = [
    "RELIANCE", "TCS", "INFY", "HDFCBANK", "ICICIBANK", "KOTAKBANK",
    "SBIN", "AXISBANK", "LT", "ITC", "HINDUNILVR", "BAJFINANCE",
    # ... add all ~180 F&O stocks
]
```

#### Task 2.2: Fetch Stock Option Chains
**File:** `backend/app/services/fyers_data.py`

Update symbol mapping to handle stocks:
```python
def get_fyers_symbol(underlying: str) -> str:
    """Convert underlying to Fyers symbol format."""
    index_map = {
        "NIFTY": "NSE:NIFTY50-INDEX",
        "BANKNIFTY": "NSE:NIFTYBANK-INDEX",
        "FINNIFTY": "NSE:FINNIFTY-INDEX",
    }
    if underlying.upper() in index_map:
        return index_map[underlying.upper()]
    # For stocks
    return f"NSE:{underlying.upper()}-EQ"
```

#### Task 2.3: Bulk Load Instruments
Create script to load all F&O instruments:
```python
# backend/scripts/load_all_fo_instruments.py
for stock in FO_STOCKS + ["NIFTY", "BANKNIFTY", "FINNIFTY"]:
    chain = get_option_chain(stock, nearest_expiry, strikecount=20)
    # Insert into database
```

### Phase 3: Strike-Level Technical Scanning (CORE FEATURE)

This is the unique value proposition of StrikeEdge.

#### Task 3.1: Fetch Strike Candles
**File:** `backend/app/services/fyers_data.py`

The `get_history()` function already works. Use it for strike symbols:
```python
# Example: Get 5-min candles for NIFTY 24000 CE
candles = get_history("NSE:NIFTY2631024000CE", resolution="5", days=5)
```

#### Task 3.2: Compute Technical Indicators
**File:** `backend/app/services/indicators.py` (create or enhance)

```python
import pandas as pd
import pandas_ta as ta

def compute_indicators(candles: list[dict], indicators: list[str]) -> dict:
    """Compute technical indicators on OHLCV data."""
    df = pd.DataFrame(candles)
    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='s')
    df.set_index('timestamp', inplace=True)
    
    results = {}
    
    if 'RSI' in indicators or 'RSI14' in indicators:
        df['rsi'] = ta.rsi(df['close'], length=14)
        results['rsi'] = df['rsi'].iloc[-1]
    
    if 'MACD' in indicators:
        macd = ta.macd(df['close'])
        results['macd'] = macd['MACD_12_26_9'].iloc[-1]
        results['macd_signal'] = macd['MACDs_12_26_9'].iloc[-1]
        results['macd_hist'] = macd['MACDh_12_26_9'].iloc[-1]
    
    if 'EMA20' in indicators:
        df['ema20'] = ta.ema(df['close'], length=20)
        results['ema20'] = df['ema20'].iloc[-1]
    
    # Add more indicators as needed
    return results
```

#### Task 3.3: Scanner Engine
**File:** `backend/app/services/scanner.py` (create or enhance)

```python
async def scan_strikes(
    underlyings: list[str],
    expiry: str,
    rules: list[dict],  # e.g., [{"indicator": "RSI14", "operator": ">", "value": 60}]
    timeframe: str = "5m"
) -> list[dict]:
    """
    Scan all option strikes and return those matching technical criteria.
    
    This is the CORE feature of StrikeEdge.
    """
    results = []
    
    for underlying in underlyings:
        # Get option chain
        chain = get_option_chain(underlying, expiry, strikecount=30)
        
        for strike in chain:
            symbol = strike['symbol']
            
            # Fetch candles for this strike
            candles = get_history(symbol, resolution=timeframe_to_resolution(timeframe))
            
            if not candles or len(candles) < 20:
                continue
            
            # Compute indicators
            indicators = compute_indicators(candles, [r['indicator'] for r in rules])
            
            # Check if all rules match
            matched = True
            for rule in rules:
                value = indicators.get(rule['indicator'].lower())
                if value is None:
                    matched = False
                    break
                if not evaluate_rule(value, rule['operator'], rule['value']):
                    matched = False
                    break
            
            if matched:
                results.append({
                    'symbol': symbol,
                    'underlying': underlying,
                    'strike_price': strike['strike_price'],
                    'option_type': strike['option_type'],
                    'ltp': strike['ltp'],
                    'oi': strike['oi'],
                    'indicators': indicators,
                })
    
    return results
```

#### Task 3.4: Scanner API Endpoint
**File:** `backend/app/api/routes_v1.py`

```python
@router.post("/scanner/technical")
async def technical_scanner(request: TechnicalScanRequest):
    """
    Scan option strikes based on technical indicator conditions.
    
    Example request:
    {
        "underlyings": ["NIFTY", "BANKNIFTY", "RELIANCE"],
        "expiry": "2026-03-10",
        "timeframe": "5m",
        "rules": [
            {"indicator": "RSI14", "operator": ">", "value": 60},
            {"indicator": "MACD", "operator": ">", "value": 0}
        ]
    }
    """
    results = await scan_strikes(
        underlyings=request.underlyings,
        expiry=request.expiry,
        rules=request.rules,
        timeframe=request.timeframe
    )
    return {"results": results, "count": len(results)}
```

### Phase 4: Frontend Scanner UI

#### Task 4.1: Enhanced Screener Builder
**File:** `frontend/web/src/features/screener/ScreenerBuilder.tsx`

Add:
- Multi-select for underlyings (NIFTY, BANKNIFTY, stocks)
- Expiry dropdown (fetched from API)
- Multiple indicator rules (add/remove)
- Operator selection (>, <, =, crosses above, crosses below)
- Timeframe selection (1m, 5m, 15m, 1h, 1D)

#### Task 4.2: Results Table with Charts
**File:** `frontend/web/src/features/screener/ScanResults.tsx`

- Show matched strikes with all indicator values
- Click to open strike chart with indicators plotted
- Sort/filter results
- Export to CSV

### Phase 5: Performance Optimization

Scanning 1000s of strikes is computationally heavy. Optimizations:

#### Task 5.1: Redis Caching
Cache candle data and indicator computations:
```python
# backend/app/services/cache.py
import redis

redis_client = redis.Redis(host='localhost', port=6379, db=0)

def get_cached_candles(symbol: str, timeframe: str) -> list | None:
    key = f"candles:{symbol}:{timeframe}"
    data = redis_client.get(key)
    return json.loads(data) if data else None

def cache_candles(symbol: str, timeframe: str, candles: list, ttl: int = 300):
    key = f"candles:{symbol}:{timeframe}"
    redis_client.setex(key, ttl, json.dumps(candles))
```

#### Task 5.2: Background Workers
Use Celery or APScheduler to:
- Pre-fetch candles for all active strikes
- Pre-compute indicators
- Store in Redis/DB for instant scanning

#### Task 5.3: WebSocket for Live Updates
Real-time price updates via Fyers WebSocket:
```python
# backend/app/services/fyers_websocket.py
from fyers_apiv3.FyersWebSocket import data_ws

def start_websocket(symbols: list[str], on_tick):
    ws = data_ws.FyersDataSocket(
        access_token=f"{app_id}:{access_token}",
        on_message=on_tick,
    )
    ws.subscribe(symbols)
    ws.connect()
```

## API Endpoints Reference

### Current Endpoints (in routes_v1.py):
```
GET  /api/v1/fyers/auth-url     # Get OAuth login URL
GET  /api/v1/fyers/status       # Check if authenticated
GET  /api/v1/fyers/spot/{underlying}  # Get spot price
GET  /api/v1/fyers/quotes       # Get quotes for symbols
GET  /api/v1/fyers/history      # Get historical candles
GET  /api/v1/options/chain      # Get options chain
GET  /api/v1/instruments        # List all instruments
POST /api/v1/scan               # Run scanner
GET  /api/v1/screeners          # List saved screeners
POST /api/v1/screeners          # Save screener
```

### Endpoints to Add:
```
GET  /api/v1/fyers/expiries/{underlying}  # Get available expiries
GET  /api/v1/fo-stocks                     # List all F&O stocks
POST /api/v1/scanner/technical             # Technical indicator scanner
GET  /api/v1/strikes/{symbol}/candles      # Strike candles with indicators
POST /api/v1/instruments/refresh           # Reload instruments from Fyers
```

## Environment Variables

### Backend (.env in root):
```
STRIKEEDGE_FYERS_APP_ID=7LAA87QF50-100
STRIKEEDGE_FYERS_SECRET_KEY=your_secret
STRIKEEDGE_FYERS_REDIRECT_URI=https://127.0.0.1:8000/callback
STRIKEEDGE_DATABASE_URL=sqlite:///./strikeedge.db

# Legacy fallbacks (also supported):
FYERS_CLIENT_ID=7LAA87QF50-100
FYERS_SECRET_KEY=your_secret
```

### Frontend (.env.local in frontend/web/):
```
NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY=pk_test_xxx
CLERK_SECRET_KEY=sk_test_xxx
NEXT_PUBLIC_API_URL=http://localhost:8000
```

## Testing Commands

```powershell
# Backend
cd C:\Users\USER\StrikeEdge\backend
python -m pytest -v                    # Run all tests
python -m uvicorn app.main:app --reload --port 8000  # Start server

# Test Fyers connection
python -c "from app.services.fyers_data import get_spot_price; print(get_spot_price('NIFTY'))"

# Test options chain
python -c "from app.services.fyers_data import get_option_chain; print(len(get_option_chain('NIFTY', '2026-03-10', 15)))"

# Frontend
cd C:\Users\USER\StrikeEdge\frontend\web
npm run dev                            # Start dev server on port 3000
npm run build                          # Production build
```

## Fyers API Notes

### Symbol Formats:
- Index: `NSE:NIFTY50-INDEX`, `NSE:NIFTYBANK-INDEX`
- Stock: `NSE:RELIANCE-EQ`
- Option: `NSE:NIFTY2631024000CE` (NIFTY 10-Mar-26 24000 CE)

### Rate Limits:
- Fyers free tier: Limited API calls
- Consider caching aggressively
- Batch requests where possible

### Expiry Timestamp:
- Fyers uses Unix timestamps for expiry
- Fetch valid expiries first, then use their timestamps
- Don't construct timestamps manually

## Database Schema

```sql
-- Instruments (options master)
CREATE TABLE instruments (
    token VARCHAR(64) PRIMARY KEY,
    symbol VARCHAR(128),
    name VARCHAR(128),
    exchange VARCHAR(16),
    instrument_type VARCHAR(32),
    underlying VARCHAR(64),
    option_type VARCHAR(8),  -- CE/PE
    strike_price FLOAT,
    expiry VARCHAR(32),
    lot_size INTEGER
);

-- Strike candles (for technical analysis)
CREATE TABLE strike_candles (
    id VARCHAR(36) PRIMARY KEY,
    token VARCHAR(64),
    timeframe VARCHAR(8),
    timestamp DATETIME,
    open FLOAT,
    high FLOAT,
    low FLOAT,
    close FLOAT,
    volume INTEGER
);

-- Computed indicators cache
CREATE TABLE indicator_cache (
    id VARCHAR(36) PRIMARY KEY,
    token VARCHAR(64),
    timeframe VARCHAR(8),
    timestamp DATETIME,
    rsi FLOAT,
    macd FLOAT,
    macd_signal FLOAT,
    ema20 FLOAT,
    -- add more as needed
);
```

## Next Immediate Steps for Cursor

1. **Fix LTP display** in Options Chain Workbench
2. **Add expiry dropdown** that fetches from Fyers
3. **Add underlying dropdown** with NIFTY, BANKNIFTY, + stocks
4. **Create technical scanner endpoint** that:
   - Accepts indicator rules
   - Fetches candles for each strike
   - Computes indicators
   - Returns matching strikes
5. **Build scanner UI** with rule builder

## Questions for the Developer

When continuing development, consider:
1. How many strikes to scan simultaneously? (Rate limit concerns)
2. How often to refresh candle data? (Real-time vs periodic)
3. Which indicators are must-have vs nice-to-have?
4. Should scanning run on-demand or continuously in background?

---

**This guide should give Cursor/Claude Code full context to continue building StrikeEdge.**
