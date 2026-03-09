from __future__ import annotations

import math


def _norm_cdf(x: float) -> float:
    return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))


def _norm_pdf(x: float) -> float:
    return (1.0 / math.sqrt(2.0 * math.pi)) * math.exp(-0.5 * x * x)


class OptionsAnalyticsService:
    @staticmethod
    def greeks(
        *,
        option_type: str,
        spot: float,
        strike: float,
        time_to_expiry_years: float,
        risk_free_rate: float,
        volatility: float,
    ) -> dict[str, float]:
        if spot <= 0 or strike <= 0 or time_to_expiry_years <= 0 or volatility <= 0:
            raise ValueError("Invalid inputs for Greeks calculation")

        sqrt_t = math.sqrt(time_to_expiry_years)
        d1 = (math.log(spot / strike) + (risk_free_rate + 0.5 * volatility * volatility) * time_to_expiry_years) / (volatility * sqrt_t)
        d2 = d1 - volatility * sqrt_t

        option_kind = option_type.upper()
        if option_kind not in {"CE", "PE"}:
            raise ValueError("option_type must be CE or PE")

        if option_kind == "CE":
            delta = _norm_cdf(d1)
            theta = (
                -(spot * _norm_pdf(d1) * volatility) / (2 * sqrt_t)
                - risk_free_rate * strike * math.exp(-risk_free_rate * time_to_expiry_years) * _norm_cdf(d2)
            ) / 365.0
            rho = (strike * time_to_expiry_years * math.exp(-risk_free_rate * time_to_expiry_years) * _norm_cdf(d2)) / 100.0
        else:
            delta = _norm_cdf(d1) - 1
            theta = (
                -(spot * _norm_pdf(d1) * volatility) / (2 * sqrt_t)
                + risk_free_rate * strike * math.exp(-risk_free_rate * time_to_expiry_years) * _norm_cdf(-d2)
            ) / 365.0
            rho = (-strike * time_to_expiry_years * math.exp(-risk_free_rate * time_to_expiry_years) * _norm_cdf(-d2)) / 100.0

        gamma = _norm_pdf(d1) / (spot * volatility * sqrt_t)
        vega = (spot * _norm_pdf(d1) * sqrt_t) / 100.0

        return {
            "delta": round(delta, 6),
            "gamma": round(gamma, 6),
            "theta": round(theta, 6),
            "vega": round(vega, 6),
            "rho": round(rho, 6),
        }


options_analytics_service = OptionsAnalyticsService()
