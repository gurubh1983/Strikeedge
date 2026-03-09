# User Feature Journey

This document describes the current user-facing flow across auth, preferences, screeners, watchlists, and alerts.

## End-to-End Flow

1. User signs in through Clerk (`/sign-in`) and accesses protected modules.
2. Frontend syncs profile and loads defaults from:
   - `GET /api/v1/api/user`
   - `GET /api/v1/user/preferences`
3. User configures preferences (timeframe, default indicator, theme) and saves with:
   - `PUT /api/v1/api/user`
   - `PUT /api/v1/user/preferences`
4. In Screener:
   - User builds a rule set and runs scans.
   - User saves a screener (`POST /api/v1/screeners`), reloads saved list, and loads a saved config into builder controls.
5. In Portfolio:
   - User creates watchlists, adds tokens, and manages favorites.
   - Watchlist updates stream over websocket (`/api/v1/ws/watchlists/{user_id}`) for near real-time UI refresh.
6. In Alerts:
   - User sets notification preferences and reviews outbox queue status.

## UX Principles Applied

- Keep controls explicit and low-friction for rapid iteration.
- Preserve context: saved screener load restores runtime parameters.
- Prefer immediate feedback with refresh actions and websocket updates where available.
