from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy.orm import Session, sessionmaker

from app.db.models import FavoriteModel, WatchlistItemModel, WatchlistModel


class WatchlistService:
    def __init__(self) -> None:
        self._session_factory: sessionmaker[Session] | None = None

    def set_session_factory(self, session_factory: sessionmaker[Session]) -> None:
        self._session_factory = session_factory

    def create_watchlist(self, *, user_id: str, name: str) -> dict:
        if self._session_factory is None:
            now = datetime.now(timezone.utc).isoformat()
            return {"id": str(uuid4()), "user_id": user_id, "name": name, "created_at": now, "tokens": []}
        with self._session_factory() as session:
            model = WatchlistModel(id=str(uuid4()), user_id=user_id, name=name, created_at=datetime.now(timezone.utc))
            session.add(model)
            session.commit()
            return {"id": model.id, "user_id": model.user_id, "name": model.name, "created_at": model.created_at.isoformat(), "tokens": []}

    def list_watchlists(self, *, user_id: str) -> list[dict]:
        if self._session_factory is None:
            return []
        with self._session_factory() as session:
            watchlists = session.query(WatchlistModel).filter(WatchlistModel.user_id == user_id).order_by(WatchlistModel.created_at.desc()).all()
            out: list[dict] = []
            for row in watchlists:
                items = session.query(WatchlistItemModel).filter(WatchlistItemModel.watchlist_id == row.id).all()
                out.append(
                    {
                        "id": row.id,
                        "user_id": row.user_id,
                        "name": row.name,
                        "created_at": row.created_at.isoformat(),
                        "tokens": [item.token for item in items],
                    }
                )
            return out

    def add_watchlist_item(self, *, watchlist_id: str, token: str) -> dict | None:
        if self._session_factory is None:
            return None
        with self._session_factory() as session:
            watchlist = session.get(WatchlistModel, watchlist_id)
            if watchlist is None:
                return None
            exists = (
                session.query(WatchlistItemModel)
                .filter(WatchlistItemModel.watchlist_id == watchlist_id)
                .filter(WatchlistItemModel.token == token)
                .first()
            )
            if exists is None:
                session.add(
                    WatchlistItemModel(
                        id=str(uuid4()),
                        watchlist_id=watchlist_id,
                        token=token,
                        created_at=datetime.now(timezone.utc),
                    )
                )
                session.commit()
            return {
                "id": watchlist.id,
                "user_id": watchlist.user_id,
                "name": watchlist.name,
                "created_at": watchlist.created_at.isoformat(),
                "tokens": [item.token for item in session.query(WatchlistItemModel).filter(WatchlistItemModel.watchlist_id == watchlist_id).all()],
            }

    def create_favorite(self, *, user_id: str, token: str) -> dict:
        if self._session_factory is None:
            return {"id": str(uuid4()), "user_id": user_id, "token": token, "created_at": datetime.now(timezone.utc).isoformat()}
        with self._session_factory() as session:
            existing = (
                session.query(FavoriteModel)
                .filter(FavoriteModel.user_id == user_id)
                .filter(FavoriteModel.token == token)
                .first()
            )
            if existing is not None:
                return {"id": existing.id, "user_id": existing.user_id, "token": existing.token, "created_at": existing.created_at.isoformat()}
            model = FavoriteModel(id=str(uuid4()), user_id=user_id, token=token, created_at=datetime.now(timezone.utc))
            session.add(model)
            session.commit()
            return {"id": model.id, "user_id": model.user_id, "token": model.token, "created_at": model.created_at.isoformat()}

    def list_favorites(self, *, user_id: str) -> list[dict]:
        if self._session_factory is None:
            return []
        with self._session_factory() as session:
            rows = session.query(FavoriteModel).filter(FavoriteModel.user_id == user_id).order_by(FavoriteModel.created_at.desc()).all()
            return [{"id": row.id, "user_id": row.user_id, "token": row.token, "created_at": row.created_at.isoformat()} for row in rows]

    def delete_favorite(self, *, user_id: str, token: str) -> bool:
        if self._session_factory is None:
            return False
        with self._session_factory() as session:
            row = (
                session.query(FavoriteModel)
                .filter(FavoriteModel.user_id == user_id)
                .filter(FavoriteModel.token == token)
                .first()
            )
            if row is None:
                return False
            session.delete(row)
            session.commit()
            return True


watchlist_service = WatchlistService()
