from __future__ import annotations

from app.core.settings import get_settings
from app.db.session import get_session_factory, init_db
from app.services.idempotency import idempotency_service


def main() -> None:
    settings = get_settings()
    init_db(settings)
    idempotency_service.set_session_factory(get_session_factory(settings))
    cleaned = idempotency_service.cleanup_expired()
    print({"cleaned_records": cleaned})


if __name__ == "__main__":
    main()
