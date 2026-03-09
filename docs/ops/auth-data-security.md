# Auth and Data Security Notes

This note captures the current authentication and user-data boundaries in StrikeEdge.

## Authentication Modes

- Backend auth resolution is centralized in `backend/app/core/auth.py`.
- Supported modes: `header`, `token`, `jwt`, and `clerk` (JWKS verification).
- For production with Clerk, set `STRIKEEDGE_AUTH_MODE=clerk` and configure Clerk JWKS/JWT settings.

## Protected UX Routes

- Frontend route protection is enforced in `frontend/web/middleware.ts` via Clerk middleware.
- Protected modules include dashboard, screener, scanner, strategy, portfolio, alerts, preferences, AI insights, and stocks.

## User Identity Mapping

- User identity is normalized as `clerk_user_id` in `users` and `user_preferences` tables.
- API routes for profile and preferences derive identity from auth context instead of user-supplied query parameters.

## Data Isolation and Ownership

- Watchlists/favorites/alerts are scoped by explicit `user_id` fields in persistent models.
- User preference retrieval and writes are scoped to authenticated identity (`/api/v1/user/preferences`).
- Integration tests verify baseline isolation behavior for preferences and watchlist retrieval.
