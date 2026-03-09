from __future__ import annotations

import argparse

from app.core.settings import get_settings
from app.db.session import get_session_factory, init_db
from app.services.notifications import notification_service


def main() -> None:
    parser = argparse.ArgumentParser(description="Dispatch pending notification outbox items.")
    parser.add_argument("--limit", type=int, default=100, help="Maximum pending records to process.")
    args = parser.parse_args()

    settings = get_settings()
    init_db(settings)
    notification_service.set_session_factory(get_session_factory(settings))
    stats = notification_service.dispatch_pending(limit=args.limit)
    print(stats)


if __name__ == "__main__":
    main()
