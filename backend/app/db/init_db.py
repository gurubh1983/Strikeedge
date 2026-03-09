from __future__ import annotations

from collections.abc import Generator

from sqlalchemy.orm import Session

from app.core.settings import get_settings
from app.db.session import get_session_factory, init_db


def init_database() -> None:
    settings = get_settings()
    init_db(settings)


def get_db_session() -> Generator[Session, None, None]:
    settings = get_settings()
    session_factory = get_session_factory(settings)
    session = session_factory()
    try:
        yield session
    finally:
        session.close()
