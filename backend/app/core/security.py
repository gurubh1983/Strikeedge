from __future__ import annotations

from fastapi import Header, HTTPException, status

from app.core.rate_limiter import rate_limit_store
from app.core.settings import get_settings

def require_actor_id(x_actor_id: str | None = Header(default=None)) -> str:
    if not x_actor_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing x-actor-id",
        )
    return x_actor_id


def require_idempotency_key(x_idempotency_key: str | None = Header(default=None)) -> str:
    if not x_idempotency_key:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing x-idempotency-key",
        )
    return x_idempotency_key


def require_rate_limit(x_actor_id: str | None = Header(default=None)) -> None:
    settings = get_settings()
    actor = x_actor_id or "anonymous"
    allowed = rate_limit_store.hit(actor=actor, limit_per_minute=settings.rate_limit_per_minute)
    if not allowed:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded",
        )
