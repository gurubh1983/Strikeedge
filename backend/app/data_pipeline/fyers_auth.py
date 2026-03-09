from __future__ import annotations

import base64
import hashlib
import hmac
import struct
import time
from dataclasses import dataclass
from typing import Any

import httpx


def fix_base32_padding(secret: str) -> str:
    """Fix Base32 padding for broker TOTP secrets."""
    secret = secret.replace(" ", "").upper()
    padding_needed = (8 - len(secret) % 8) % 8
    return secret + ("=" * padding_needed)


def generate_totp(secret_base32: str, time_step: int = 30, digits: int = 6, for_time: int | None = None) -> str:
    now = int(for_time if for_time is not None else time.time())
    counter = now // time_step
    normalized_secret = fix_base32_padding(secret_base32)
    key = base64.b32decode(normalized_secret, casefold=True)
    msg = struct.pack(">Q", counter)
    digest = hmac.new(key, msg, hashlib.sha1).digest()
    offset = digest[-1] & 0x0F
    code = struct.unpack(">I", digest[offset : offset + 4])[0] & 0x7FFFFFFF
    otp = code % (10**digits)
    return str(otp).zfill(digits)


@dataclass(slots=True)
class FyersSession:
    access_token: str
    refresh_token: str | None


class FyersAuthClient:
    def __init__(self, base_url: str = "https://api-t1.fyers.in/api/v3", timeout_seconds: float = 20.0) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout_seconds = timeout_seconds

    async def create_session(
        self,
        app_id: str,
        secret_key: str,
        redirect_uri: str,
        totp_secret: str,
    ) -> FyersSession:
        totp = generate_totp(totp_secret)
        payload = {
            "app_id": app_id,
            "secret_key": secret_key,
            "redirect_uri": redirect_uri,
            "grant_type": "client_credentials",
            "totp": totp,
        }
        async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
            response = await client.post(f"{self.base_url}/token", json=payload)
            response.raise_for_status()
            body: dict[str, Any] = response.json()
        access_token = str(body.get("access_token") or body.get("token") or "").strip()
        if not access_token:
            raise ValueError("Missing access_token in Fyers OAuth response")
        return FyersSession(access_token=access_token, refresh_token=(str(body.get("refresh_token", "")).strip() or None))

    @staticmethod
    def build_ws_headers(session: FyersSession, app_id: str) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {session.access_token}",
            "x-api-key": app_id,
        }

    @staticmethod
    def build_oauth_session(
        app_id: str,
        secret_key: str,
        redirect_uri: str,
    ) -> "FyersSessionModelWrapper":
        """Build SessionModel for OAuth auth_code flow. Returns wrapper with generate_authcode and generate_token."""
        try:
            from fyers_apiv3 import fyersModel
            sm = fyersModel.SessionModel(
                client_id=app_id,
                redirect_uri=redirect_uri,
                response_type="code",
                scope="",
                state="strikeedge",
                secret_key=secret_key,
                grant_type="authorization_code",
            )
            return FyersSessionModelWrapper(sm)
        except Exception as e:
            raise ValueError(f"Failed to init Fyers SessionModel: {e}") from e

    @staticmethod
    async def exchange_auth_code(
        app_id: str,
        secret_key: str,
        redirect_uri: str,
        auth_code: str,
    ) -> FyersSession:
        """Exchange auth_code from OAuth callback for access_token."""
        try:
            from fyers_apiv3 import fyersModel
            sm = fyersModel.SessionModel(
                client_id=app_id,
                redirect_uri=redirect_uri,
                response_type="code",
                scope="",
                state="strikeedge",
                secret_key=secret_key,
                grant_type="authorization_code",
            )
            sm.set_token(auth_code)
            resp = sm.generate_token()
            if not isinstance(resp, dict):
                raise ValueError("Invalid token response")
            access_token = str(resp.get("access_token") or resp.get("s") or "").strip()
            if not access_token:
                raise ValueError(resp.get("message", "Missing access_token in response"))
            return FyersSession(access_token=access_token, refresh_token=str(resp.get("refresh_token", "") or "").strip() or None)
        except Exception as e:
            raise ValueError(f"Token exchange failed: {e}") from e


class FyersSessionModelWrapper:
    """Thin wrapper to expose generate_authcode from fyers SessionModel."""

    def __init__(self, session_model) -> None:
        self._sm = session_model

    def generate_authcode(self) -> str:
        return self._sm.generate_authcode()
