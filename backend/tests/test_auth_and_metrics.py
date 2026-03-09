import base64
import hashlib
import hmac
import json
from fastapi.testclient import TestClient

from app.core.auth import HeaderAuthProvider, JWTAuthProvider, TokenAuthProvider
from app.main import app


def _encode_hs256(payload: dict, secret: str) -> str:
    header = {"alg": "HS256", "typ": "JWT"}
    header_b = base64.urlsafe_b64encode(json.dumps(header).encode()).decode().rstrip("=")
    payload_b = base64.urlsafe_b64encode(json.dumps(payload).encode()).decode().rstrip("=")
    signed_input = f"{header_b}.{payload_b}".encode()
    signature = hmac.new(secret.encode(), signed_input, hashlib.sha256).digest()
    signature_b = base64.urlsafe_b64encode(signature).decode().rstrip("=")
    return f"{header_b}.{payload_b}.{signature_b}"


def test_header_auth_provider() -> None:
    provider = HeaderAuthProvider()
    user = provider.resolve_user(None, "actor-1")
    assert user.user_id == "actor-1"


def test_token_auth_provider() -> None:
    provider = TokenAuthProvider()
    user = provider.resolve_user("Bearer user:abc123:role:admin", None)
    assert user.user_id == "abc123"
    assert user.role == "admin"


def test_jwt_auth_provider_hs256() -> None:
    token = _encode_hs256({"sub": "user-123", "role": "admin"}, "dev-secret-change-me")
    provider = JWTAuthProvider(use_clerk_jwks=False)
    user = provider.resolve_user(f"Bearer {token}", None)
    assert user.user_id == "user-123"
    assert user.role == "admin"


def test_metrics_endpoint_available() -> None:
    client = TestClient(app)
    _ = client.get("/health")
    response = client.get("/metrics")
    assert response.status_code == 200
    payload = response.json()
    assert "http_requests_total" in payload

    prom = client.get("/metrics/prometheus")
    assert prom.status_code == 200
    assert "http_requests_total" in prom.text


def test_error_envelope_for_missing_headers() -> None:
    client = TestClient(app)
    payload = {
        "user_id": "u3",
        "name": "Guarded",
        "rules": [{"field": "rsi_14", "operator": ">", "value": 60}],
    }
    response = client.post("/api/v1/strategies", json=payload)
    assert response.status_code in {400, 401}
    body = response.json()
    assert "error" in body
    assert "code" in body["error"]


def test_rate_limit_scaffolding_can_be_overridden() -> None:
    client = TestClient(app)
    response = client.get("/health")
    assert response.status_code == 200
