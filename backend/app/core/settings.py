from __future__ import annotations

import os
from functools import lru_cache
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


def _fyers_env(key: str, default: str | None = None) -> str | None:
    """Read Fyers config from STRIKEEDGE_FYERS_* or fallback to FYERS_* (without prefix)."""
    val = os.environ.get(f"STRIKEEDGE_FYERS_{key}")
    if val and str(val).strip():
        return str(val).strip()
    legacy = os.environ.get(f"FYERS_{key}")
    if legacy and str(legacy).strip():
        return str(legacy).strip()
    alt = {"APP_ID": "CLIENT_ID"}.get(key)
    if alt:
        legacy = os.environ.get(f"FYERS_{alt}") or os.environ.get(f"YERS_CLIENT_ID")
        if legacy and str(legacy).strip():
            return str(legacy).strip()
    return default


class AppSettings(BaseSettings):
    model_config = SettingsConfigDict(env_file=(".env", "../.env"), env_prefix="STRIKEEDGE_", extra="ignore")

    app_name: str = "StrikeEdge API"
    app_version: str = "1.0.0"
    environment: Literal["dev", "staging", "preprod", "prod"] = "dev"
    database_url: str = "sqlite:///./strikeedge.db"
    auth_mode: Literal["header", "token", "jwt", "clerk"] = "header"
    jwt_secret: str = "dev-secret-change-me"
    jwt_algorithm: str = "HS256"
    jwt_public_key: str | None = None
    jwt_audience: str | None = None
    jwt_issuer: str | None = None
    clerk_jwks_url: str | None = None
    rate_limit_per_minute: int = 120
    rate_limit_backend: Literal["memory", "redis"] = "memory"
    redis_url: str | None = None
    idempotency_ttl_seconds: int = 86400
    fyers_app_id: str | None = None
    fyers_secret_key: str | None = None
    fyers_redirect_uri: str | None = None
    fyers_totp_secret: str | None = None
    fyers_rest_base_url: str = "https://api-t1.fyers.in/api/v3"
    fyers_ws_base_url: str = "wss://rtsocket-api.fyers.in/versova"
    notifications_email_provider: Literal["mock", "ses"] = "mock"

    @property
    def fyers_app_id_resolved(self) -> str | None:
        return (self.fyers_app_id and str(self.fyers_app_id).strip()) or _fyers_env("APP_ID")

    @property
    def fyers_secret_key_resolved(self) -> str | None:
        return (self.fyers_secret_key and str(self.fyers_secret_key).strip()) or _fyers_env("SECRET_KEY")

    @property
    def fyers_redirect_uri_resolved(self) -> str | None:
        return (self.fyers_redirect_uri and str(self.fyers_redirect_uri).strip()) or _fyers_env("REDIRECT_URI") or "https://127.0.0.1:8000/callback"

    @property
    def fyers_totp_secret_resolved(self) -> str | None:
        return (self.fyers_totp_secret and str(self.fyers_totp_secret).strip()) or _fyers_env("TOTP_SECRET")
    notifications_push_provider: Literal["mock", "firebase"] = "mock"
    aws_ses_from_email: str | None = None
    firebase_project_id: str | None = None


@lru_cache
def get_settings() -> AppSettings:
    return AppSettings()
