from __future__ import annotations

import pytest

from app.core.settings import AppSettings
from app.core.startup_checks import validate_runtime_settings


def test_startup_checks_allow_empty_fyers_config() -> None:
    settings = AppSettings()
    validate_runtime_settings(settings)


def test_startup_checks_reject_partial_fyers_config() -> None:
    settings = AppSettings(
        fyers_app_id="x",
        fyers_secret_key=None,
        fyers_redirect_uri=None,
        fyers_totp_secret=None,
    )
    with pytest.raises(ValueError):
        validate_runtime_settings(settings)


def test_startup_checks_accept_unpadded_totp_secret() -> None:
    settings = AppSettings(
        fyers_app_id="XG1234-100",
        fyers_secret_key="secret",
        fyers_redirect_uri="http://localhost:8080/",
        fyers_totp_secret="GRDQAVJ7YI6NE6ECSLNEG7VBSE",
    )
    validate_runtime_settings(settings)
