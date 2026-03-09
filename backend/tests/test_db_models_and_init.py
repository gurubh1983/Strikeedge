from __future__ import annotations

from pathlib import Path

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from app.db.models import Base, InstrumentModel


def test_sqlite_created_and_insert_query(tmp_path: Path) -> None:
    db_path = tmp_path / "test.db"
    engine = create_engine(f"sqlite:///{db_path}", future=True)
    Base.metadata.create_all(bind=engine)
    assert db_path.exists()

    SessionLocal = sessionmaker(bind=engine, future=True)
    with SessionLocal() as session:
        session.add(
            InstrumentModel(
                token="TK1",
                symbol="NIFTY24APR24000CE",
                name="NIFTY",
                exchange="NFO",
                instrument_type="OPTIDX",
                underlying="NIFTY",
                option_type="CE",
                strike_price=24000,
                expiry="2026-04-24",
                lot_size=50,
            )
        )
        session.commit()

    with SessionLocal() as session:
        row = session.query(InstrumentModel).filter(InstrumentModel.underlying == "NIFTY").first()
        assert row is not None
        assert row.token == "TK1"
