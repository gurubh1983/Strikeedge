from __future__ import annotations

from app.core.rate_limiter import InMemoryRateLimitStore, RedisRateLimitStore
from app.data_pipeline.fyers_auth import FyersAuthClient, FyersSession, fix_base32_padding, generate_totp


def test_generate_totp_is_six_digits() -> None:
    # RFC6238 test secret in base32 for deterministic format check
    code = generate_totp("JBSWY3DPEHPK3PXP", for_time=1700000000)
    assert len(code) == 6
    assert code.isdigit()


def test_fix_base32_padding_handles_spaces_case_and_padding() -> None:
    raw = "grdq avj7 yi6n e6ec slne g7vbse"
    fixed = fix_base32_padding(raw)
    assert " " not in fixed
    assert fixed == fixed.upper()
    assert len(fixed) % 8 == 0
    assert fixed.endswith("=")


def test_generate_totp_accepts_unpadded_secret() -> None:
    unpadded = "GRDQAVJ7YI6NE6ECSLNEG7VBSE"
    padded = "GRDQAVJ7YI6NE6ECSLNEG7VBSE======"
    code_unpadded = generate_totp(unpadded, for_time=1700000000)
    code_padded = generate_totp(padded, for_time=1700000000)
    assert code_unpadded == code_padded


def test_build_ws_headers() -> None:
    session = FyersSession(access_token="token", refresh_token="r")
    headers = FyersAuthClient.build_ws_headers(session=session, app_id="app")
    assert headers["Authorization"] == "Bearer token"
    assert headers["x-api-key"] == "app"


def test_inmemory_rate_limit_store() -> None:
    store = InMemoryRateLimitStore()
    assert store.hit("u1", 2) is True
    assert store.hit("u1", 2) is True
    assert store.hit("u1", 2) is False


def test_redis_rate_limit_fallback_without_connection() -> None:
    store = RedisRateLimitStore(redis_url="redis://127.0.0.1:6399/0")
    assert store.hit("u2", 1) is True
    assert store.hit("u2", 1) is False
