from __future__ import annotations

from functools import lru_cache

from sqlalchemy import Engine, create_engine, text
from sqlalchemy.orm import Session, sessionmaker

from app.core.settings import AppSettings
from app.db.models import Base


@lru_cache
def get_engine(database_url: str) -> Engine:
    return create_engine(database_url, future=True)


def get_session_factory(settings: AppSettings) -> sessionmaker[Session]:
    engine = get_engine(settings.database_url)
    return sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)


def init_db(settings: AppSettings) -> None:
    engine = get_engine(settings.database_url)
    Base.metadata.create_all(bind=engine)
    _ensure_options_chain_columns(engine)


def _ensure_options_chain_columns(engine: Engine) -> None:
    if not str(engine.url).startswith("sqlite"):
        return
    required_columns = {
        "call_oi": "INTEGER",
        "call_iv": "FLOAT",
        "put_oi": "INTEGER",
        "put_iv": "FLOAT",
        "put_call_ratio": "FLOAT",
        "total_oi_change": "INTEGER",
    }
    with engine.begin() as conn:
        tables = conn.execute(text("SELECT name FROM sqlite_master WHERE type='table' AND name='options_chain'")).fetchall()
        if not tables:
            return
        existing_cols = conn.execute(text("PRAGMA table_info(options_chain)")).fetchall()
        existing_names = {str(row[1]) for row in existing_cols}
        for col_name, col_type in required_columns.items():
            if col_name in existing_names:
                continue
            conn.execute(text(f"ALTER TABLE options_chain ADD COLUMN {col_name} {col_type}"))
