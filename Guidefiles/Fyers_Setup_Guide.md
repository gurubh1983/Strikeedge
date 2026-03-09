# Fyers API Setup Guide – StrikeEdge

## Step 1: Fyers Authentication

### Option A: OAuth (Recommended – Manual login, no TOTP)

1. **Ensure .env has:**
   ```
   STRIKEEDGE_FYERS_APP_ID=XG00420
   STRIKEEDGE_FYERS_SECRET_KEY=F0AQSZXZ6E-102
   STRIKEEDGE_FYERS_REDIRECT_URI=https://127.0.0.1:8000/callback
   ```

2. **Start the backend:**
   ```bash
   cd backend && uvicorn app.main:app --reload
   ```

3. **Get the login URL:**
   ```bash
   curl http://localhost:8000/api/v1/fyers/auth-url
   ```
   Returns `{"auth_url": "https://api-t1.fyers.in/...", ...}`

4. **Open `auth_url` in your browser** – log in with your Fyers credentials (user ID, password, PIN if asked).

5. **After login** – you’ll be redirected to `https://127.0.0.1:8000/callback?auth_code=...`. The backend exchanges `auth_code` for an access token and stores it at `~/.strikeedge/fyers_token.json`, then redirects you to the frontend.

6. **Verify:**
   ```bash
   curl http://localhost:8000/api/v1/fyers/status
   ```
   Response: `{"authenticated": true, "has_token": true}`

### Option B: TOTP (Automated, for scripts)

If you have a TOTP secret (e.g. from Google Authenticator for Fyers):

```
STRIKEEDGE_FYERS_TOTP_SECRET=your_base32_totp_secret
```

Then `run_ws_ingest.py` can log in without a browser.

---

## Step 2: Fetch Real Data

### Spot prices (NIFTY, BANKNIFTY)

```bash
curl "http://localhost:8000/api/v1/fyers/spot/NIFTY"
curl "http://localhost:8000/api/v1/fyers/spot/BANKNIFTY"
```

### Options chain (with real OI, LTP)

1. Refresh the chain (requires token):
   ```bash
   curl "http://localhost:8000/api/v1/options/chain?underlying=NIFTY&expiry=2026-04-24&refresh=true"
   ```

2. The chain is stored in the DB and returned. Use `refresh=true` to fetch fresh data from Fyers.

### Historical candles

```bash
curl "http://localhost:8000/api/v1/fyers/history?symbol=NSE:NIFTY24APR24000CE&resolution=5&days=30"
```

---

## Step 3: Connect to Frontend

### API endpoints for the UI

| Endpoint | Purpose |
|----------|---------|
| `GET /api/v1/fyers/status` | Check if Fyers is authenticated |
| `GET /api/v1/fyers/auth-url` | Get OAuth login URL |
| `GET /api/v1/fyers/spot/{underlying}` | NIFTY or BANKNIFTY spot |
| `GET /api/v1/options/chain?underlying=NIFTY&expiry=YYYY-MM-DD&refresh=true` | Options chain (real OI when authenticated) |
| `GET /api/v1/fyers/history?symbol=...&resolution=5&days=30` | Historical candles |

### Frontend flow

1. On load, call `GET /api/v1/fyers/status`.
2. If `authenticated: false`, show “Connect Fyers” button that opens `GET /api/v1/fyers/auth-url` → user visits the returned URL.
3. After OAuth, user is redirected to `/?fyers_auth=success`. Detect this and refresh data.
4. Use `/api/v1/fyers/spot/NIFTY` for spot, `/api/v1/options/chain?...&refresh=true` for the chain.
5. Screener uses the same options chain endpoint; with Fyers connected it uses real data.

---

## Troubleshooting

- **503 “Fyers credentials not configured”** – Check `STRIKEEDGE_FYERS_APP_ID`, `STRIKEEDGE_FYERS_SECRET_KEY`, `STRIKEEDGE_FYERS_REDIRECT_URI` in `.env`.
- **503 “Fyers not authenticated”** on spot/quotes – Run the OAuth flow first (Steps 1.3–1.5).
- **Token expired** – Fyers tokens usually last one day. Run the OAuth flow again to get a new token.
- **Redirect URI mismatch** – Ensure `STRIKEEDGE_FYERS_REDIRECT_URI` matches exactly what is set in your Fyers app at https://myapi.fyers.in/dashboard (including https, no trailing slash).
