from __future__ import annotations

import base64
import hashlib
import hmac
import json
from dataclasses import dataclass
from typing import Protocol

from fastapi import Header, HTTPException, status

from app.core.settings import get_settings

try:
    import jwt  # type: ignore[import-not-found]
    from jwt import PyJWKClient  # type: ignore[import-not-found]
except Exception:  # pragma: no cover - fallback path for local envs without pyjwt
    jwt = None
    PyJWKClient = None


@dataclass(slots=True)
class UserContext:
    user_id: str
    role: str = "user"


class AuthProvider(Protocol):
    def resolve_user(self, bearer_token: str | None, actor_id: str | None) -> UserContext:
        ...


class HeaderAuthProvider:
    """
    Phase 0 auth abstraction: use headers now, swap to Clerk/JWT later.
    """

    def resolve_user(self, bearer_token: str | None, actor_id: str | None) -> UserContext:
        if actor_id:
            return UserContext(user_id=actor_id)
        if bearer_token:
            token = bearer_token.replace("Bearer ", "").strip()
            if token:
                return UserContext(user_id=f"token:{token[:8]}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authentication context",
        )


class TokenAuthProvider:
    """
    Token-mode parser for Phase 0.2.
    Accepts: "Bearer user:<id>" or "Bearer user:<id>:role:<role>"
    """

    def resolve_user(self, bearer_token: str | None, actor_id: str | None) -> UserContext:
        del actor_id
        if not bearer_token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Missing bearer token",
            )
        token = bearer_token.replace("Bearer ", "").strip()
        if not token.startswith("user:"):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token format",
            )
        parts = token.split(":")
        if len(parts) < 2 or not parts[1]:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token subject",
            )
        user_id = parts[1]
        role = "user"
        if len(parts) >= 4 and parts[2] == "role" and parts[3]:
            role = parts[3]
        return UserContext(user_id=user_id, role=role)


class JWTAuthProvider:
    def __init__(self, use_clerk_jwks: bool = False) -> None:
        self.use_clerk_jwks = use_clerk_jwks

    def resolve_user(self, bearer_token: str | None, actor_id: str | None) -> UserContext:
        del actor_id
        if not bearer_token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Missing bearer token",
            )
        token = bearer_token.replace("Bearer ", "").strip()
        if not token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Missing bearer token",
            )
        settings = get_settings()
        claims = self._decode_claims(token, settings)
        user_id = claims.get("sub") or claims.get("user_id")
        if not isinstance(user_id, str) or not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token missing subject",
            )
        role = claims.get("role", "user")
        if not isinstance(role, str) or not role:
            role = "user"
        return UserContext(user_id=user_id, role=role)

    def _decode_claims(self, token: str, settings) -> dict:
        if jwt is None:
            return self._decode_hs256_without_pyjwt(token, settings.jwt_secret)
        try:
            options = {"verify_aud": bool(settings.jwt_audience)}
            if self.use_clerk_jwks:
                if not settings.clerk_jwks_url:
                    raise HTTPException(
                        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                        detail="Missing Clerk JWKS URL",
                    )
                if PyJWKClient is None:
                    raise HTTPException(
                        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                        detail="PyJWT is required for Clerk JWKS verification",
                    )
                signing_key = PyJWKClient(settings.clerk_jwks_url).get_signing_key_from_jwt(token)
                return jwt.decode(
                    token,
                    signing_key.key,
                    algorithms=["RS256"],
                    audience=settings.jwt_audience,
                    issuer=settings.jwt_issuer,
                    options=options,
                )

            decode_key: str = settings.jwt_secret
            if settings.jwt_algorithm.upper().startswith("RS") and settings.jwt_public_key:
                decode_key = settings.jwt_public_key
            return jwt.decode(
                token,
                decode_key,
                algorithms=[settings.jwt_algorithm],
                audience=settings.jwt_audience,
                issuer=settings.jwt_issuer,
                options=options,
            )
        except jwt.PyJWTError as exc:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid bearer token",
            ) from exc

    @staticmethod
    def _decode_hs256_without_pyjwt(token: str, secret: str) -> dict:
        try:
            header_b64, payload_b64, signature_b64 = token.split(".")
            signed_input = f"{header_b64}.{payload_b64}".encode()
            expected = hmac.new(secret.encode(), signed_input, hashlib.sha256).digest()
            expected_b64 = base64.urlsafe_b64encode(expected).decode().rstrip("=")
            if not hmac.compare_digest(expected_b64, signature_b64):
                raise ValueError("signature mismatch")

            padded = payload_b64 + "=" * (-len(payload_b64) % 4)
            payload_raw = base64.urlsafe_b64decode(padded.encode()).decode()
            payload = json.loads(payload_raw)
            if not isinstance(payload, dict):
                raise ValueError("invalid payload")
            return payload
        except Exception as exc:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid bearer token",
            ) from exc


def _resolve_provider() -> AuthProvider:
    settings = get_settings()
    if settings.auth_mode == "token":
        return TokenAuthProvider()
    if settings.auth_mode == "jwt":
        return JWTAuthProvider(use_clerk_jwks=False)
    if settings.auth_mode == "clerk":
        return JWTAuthProvider(use_clerk_jwks=True)
    return HeaderAuthProvider()


def require_user_context(
    authorization: str | None = Header(default=None),
    x_actor_id: str | None = Header(default=None),
) -> UserContext:
    provider = _resolve_provider()
    return provider.resolve_user(authorization, x_actor_id)
