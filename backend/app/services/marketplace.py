from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy.orm import Session, sessionmaker

from app.db.models import MarketplaceStrategyModel


class MarketplaceService:
    def __init__(self) -> None:
        self._session_factory: sessionmaker[Session] | None = None

    def set_session_factory(self, session_factory: sessionmaker[Session]) -> None:
        self._session_factory = session_factory

    def publish_strategy(self, *, strategy_id: str, owner_id: str, title: str, description: str, tags: list[str]) -> dict:
        if self._session_factory is None:
            now = datetime.now(timezone.utc).isoformat()
            return {
                "id": str(uuid4()),
                "strategy_id": strategy_id,
                "owner_id": owner_id,
                "title": title,
                "description": description,
                "tags": tags,
                "share_code": str(uuid4()),
                "created_at": now,
            }
        with self._session_factory() as session:
            model = MarketplaceStrategyModel(
                id=str(uuid4()),
                strategy_id=strategy_id,
                owner_id=owner_id,
                title=title,
                description=description,
                tags=tags,
                share_code=str(uuid4()),
                created_at=datetime.now(timezone.utc),
            )
            session.add(model)
            session.commit()
            return {
                "id": model.id,
                "strategy_id": model.strategy_id,
                "owner_id": model.owner_id,
                "title": model.title,
                "description": model.description,
                "tags": model.tags,
                "share_code": model.share_code,
                "created_at": model.created_at.isoformat(),
            }

    def list_marketplace(self, *, limit: int = 100) -> list[dict]:
        if self._session_factory is None:
            return []
        with self._session_factory() as session:
            rows = session.query(MarketplaceStrategyModel).order_by(MarketplaceStrategyModel.created_at.desc()).limit(limit).all()
            return [
                {
                    "id": row.id,
                    "strategy_id": row.strategy_id,
                    "owner_id": row.owner_id,
                    "title": row.title,
                    "description": row.description,
                    "tags": row.tags,
                    "share_code": row.share_code,
                    "created_at": row.created_at.isoformat(),
                }
                for row in rows
            ]

    def get_by_share_code(self, *, share_code: str) -> dict | None:
        if self._session_factory is None:
            return None
        with self._session_factory() as session:
            row = session.query(MarketplaceStrategyModel).filter(MarketplaceStrategyModel.share_code == share_code).first()
            if row is None:
                return None
            return {
                "id": row.id,
                "strategy_id": row.strategy_id,
                "owner_id": row.owner_id,
                "title": row.title,
                "description": row.description,
                "tags": row.tags,
                "share_code": row.share_code,
                "created_at": row.created_at.isoformat(),
            }


marketplace_service = MarketplaceService()
