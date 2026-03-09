"""Fyers access token storage for reuse during the day."""

from __future__ import annotations

import json
import os
from pathlib import Path


DEFAULT_TOKEN_FILE = Path.home() / ".strikeedge" / "fyers_token.json"


def get_token_path() -> Path:
    return Path(os.environ.get("STRIKEEDGE_FYERS_TOKEN_FILE", str(DEFAULT_TOKEN_FILE)))


def load_token() -> str | None:
    path = get_token_path()
    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text())
        return str(data.get("access_token", "")).strip() or None
    except Exception:
        return None


def save_token(access_token: str, refresh_token: str | None = None) -> None:
    path = get_token_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    data = {"access_token": access_token, "refresh_token": refresh_token}
    path.write_text(json.dumps(data, indent=2))
    os.chmod(path, 0o600)


def clear_token() -> None:
    path = get_token_path()
    if path.exists():
        path.unlink(missing_ok=True)
