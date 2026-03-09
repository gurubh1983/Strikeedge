from __future__ import annotations

import argparse

from app.core.settings import get_settings
from app.db.session import get_session_factory, init_db
from app.services.options_volatility import options_volatility_service


def main() -> None:
    parser = argparse.ArgumentParser(description="Calculate and persist strike greeks for an options chain")
    parser.add_argument("--underlying", required=True)
    parser.add_argument("--expiry", required=True)
    parser.add_argument("--spot", type=float, required=True)
    parser.add_argument("--time-to-expiry-years", type=float, required=True)
    parser.add_argument("--risk-free-rate", type=float, default=0.06)
    args = parser.parse_args()

    settings = get_settings()
    init_db(settings)
    session_factory = get_session_factory(settings)
    options_volatility_service.set_session_factory(session_factory)

    calculated = options_volatility_service.calculate_greeks_for_chain(
        underlying=args.underlying,
        expiry=args.expiry,
        spot=args.spot,
        time_to_expiry_years=args.time_to_expiry_years,
        risk_free_rate=args.risk_free_rate,
    )
    print(
        {
            "status": "ok",
            "underlying": args.underlying.upper(),
            "expiry": args.expiry,
            "calculated": calculated,
        }
    )


if __name__ == "__main__":
    main()
