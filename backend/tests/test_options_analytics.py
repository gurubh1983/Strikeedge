from __future__ import annotations

from app.services.options_analytics import options_analytics_service


def test_greeks_call_basic() -> None:
    out = options_analytics_service.greeks(
        option_type="CE",
        spot=24000,
        strike=24000,
        time_to_expiry_years=20 / 365,
        risk_free_rate=0.06,
        volatility=0.2,
    )
    assert 0 < out["delta"] < 1
    assert out["gamma"] > 0


def test_greeks_put_basic() -> None:
    out = options_analytics_service.greeks(
        option_type="PE",
        spot=24000,
        strike=24000,
        time_to_expiry_years=20 / 365,
        risk_free_rate=0.06,
        volatility=0.2,
    )
    assert -1 < out["delta"] < 0
