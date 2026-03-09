from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timedelta, timezone
from threading import Lock

from app.core.settings import get_settings

try:
    import redis  # type: ignore[import-not-found]
except Exception:  # pragma: no cover
    redis = None


class RateLimitStore:
    def hit(self, actor: str, limit_per_minute: int) -> bool:
        raise NotImplementedError


class InMemoryRateLimitStore(RateLimitStore):
    def __init__(self) -> None:
        self._lock = Lock()
        self._counters: dict[str, list[datetime]] = defaultdict(list)

    def hit(self, actor: str, limit_per_minute: int) -> bool:
        now = datetime.now(timezone.utc)
        window_start = now - timedelta(minutes=1)
        with self._lock:
            current = [ts for ts in self._counters[actor] if ts >= window_start]
            allowed = len(current) < limit_per_minute
            if allowed:
                current.append(now)
            self._counters[actor] = current
            return allowed


class RedisRateLimitStore(RateLimitStore):
    def __init__(self, redis_url: str | None = None) -> None:
        self._redis_url = redis_url
        self._client = None
        self._fallback = InMemoryRateLimitStore()
        if redis is not None and redis_url:
            try:
                self._client = redis.Redis.from_url(redis_url, decode_responses=True)
                self._client.ping()
            except Exception:
                self._client = None

    def hit(self, actor: str, limit_per_minute: int) -> bool:
        if self._client is None:
            return self._fallback.hit(actor, limit_per_minute)
        key = f"rl:{actor}"
        try:
            current = self._client.incr(key)
            if current == 1:
                self._client.expire(key, 60)
            return int(current) <= limit_per_minute
        except Exception:
            # Avoid hard-failing request path when redis is unavailable.
            return self._fallback.hit(actor, limit_per_minute)


def build_rate_limit_store() -> RateLimitStore:
    settings = get_settings()
    if settings.rate_limit_backend == "redis":
        return RedisRateLimitStore(redis_url=settings.redis_url)
    return InMemoryRateLimitStore()


rate_limit_store = build_rate_limit_store()
