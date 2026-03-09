from __future__ import annotations

import pickle
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any


class FileCache:
    def __init__(self, cache_dir: str = "./cache") -> None:
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def _path(self, key: str) -> Path:
        safe_key = key.replace("/", "_").replace(":", "_")
        return self.cache_dir / f"{safe_key}.cache"

    def set(self, key: str, value: Any, ttl_seconds: int = 3600) -> None:
        payload = {
            "value": value,
            "expires_at": (datetime.now(timezone.utc) + timedelta(seconds=ttl_seconds)).isoformat(),
        }
        with self._path(key).open("wb") as fh:
            pickle.dump(payload, fh)

    def get(self, key: str) -> Any | None:
        path = self._path(key)
        if not path.exists():
            return None
        try:
            with path.open("rb") as fh:
                payload = pickle.load(fh)
            expires_at = datetime.fromisoformat(payload["expires_at"])
            if datetime.now(timezone.utc) > expires_at:
                path.unlink(missing_ok=True)
                return None
            return payload["value"]
        except Exception:
            return None

    def delete(self, key: str) -> None:
        self._path(key).unlink(missing_ok=True)
