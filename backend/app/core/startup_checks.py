from __future__ import annotations

from app.core.settings import AppSettings
from app.data_pipeline.fyers_auth import generate_totp


def validate_runtime_settings(settings: AppSettings) -> None:
    app_id = settings.fyers_app_id
    secret = settings.fyers_secret_key
    redirect_uri = settings.fyers_redirect_uri
    totp = settings.fyers_totp_secret
    has_oauth = bool(app_id and secret and redirect_uri)
    has_totp = bool(totp)
    has_any = has_oauth or has_totp or any([app_id, secret, redirect_uri, totp])
    if has_any and not has_oauth and not has_totp:
        raise ValueError(
            "Fyers credentials are partially configured. "
            "Set STRIKEEDGE_FYERS_APP_ID, SECRET_KEY, REDIRECT_URI for OAuth, or add TOTP_SECRET for automated login."
        )
    if has_totp and not has_oauth:
        raise ValueError(
            "Fyers TOTP requires APP_ID, SECRET_KEY, REDIRECT_URI as well."
        )
    if settings.fyers_totp_secret:
        try:
            _ = generate_totp(settings.fyers_totp_secret)
        except Exception as exc:  # pragma: no cover
            raise ValueError("Invalid STRIKEEDGE_FYERS_TOTP_SECRET format") from exc
