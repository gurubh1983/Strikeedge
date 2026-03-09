from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy.orm import Session, sessionmaker

from app.db.models import UserModel, UserPreferenceModel


class UserService:
    def __init__(self) -> None:
        self._session_factory: sessionmaker[Session] | None = None
        self._users_memory: dict[str, dict] = {}
        self._prefs_memory: dict[str, dict] = {}

    def set_session_factory(self, session_factory: sessionmaker[Session]) -> None:
        self._session_factory = session_factory

    def upsert_user(self, *, clerk_user_id: str, email: str | None, display_name: str | None) -> dict:
        if self._session_factory is None:
            existing = self._users_memory.get(clerk_user_id)
            now = datetime.now(timezone.utc).isoformat()
            if existing is None:
                row = {
                    "id": str(uuid4()),
                    "clerk_user_id": clerk_user_id,
                    "email": email,
                    "display_name": display_name,
                    "created_at": now,
                    "updated_at": now,
                }
            else:
                row = {
                    **existing,
                    "email": email,
                    "display_name": display_name,
                    "updated_at": now,
                }
            self._users_memory[clerk_user_id] = row
            return row
        with self._session_factory() as session:
            row = session.query(UserModel).filter(UserModel.clerk_user_id == clerk_user_id).first()
            if row is None:
                now = datetime.now(timezone.utc)
                row = UserModel(
                    id=str(uuid4()),
                    clerk_user_id=clerk_user_id,
                    email=email,
                    display_name=display_name,
                    created_at=now,
                    updated_at=now,
                )
                session.add(row)
            else:
                row.email = email
                row.display_name = display_name
                row.updated_at = datetime.now(timezone.utc)
            session.commit()
            return {
                "id": row.id,
                "clerk_user_id": row.clerk_user_id,
                "email": row.email,
                "display_name": row.display_name,
                "created_at": row.created_at.isoformat(),
                "updated_at": row.updated_at.isoformat(),
            }

    def get_user(self, *, clerk_user_id: str) -> dict | None:
        if self._session_factory is None:
            return self._users_memory.get(clerk_user_id)
        with self._session_factory() as session:
            row = session.query(UserModel).filter(UserModel.clerk_user_id == clerk_user_id).first()
            if row is None:
                return None
            return {
                "id": row.id,
                "clerk_user_id": row.clerk_user_id,
                "email": row.email,
                "display_name": row.display_name,
                "created_at": row.created_at.isoformat(),
                "updated_at": row.updated_at.isoformat(),
            }

    def upsert_preferences(
        self,
        *,
        clerk_user_id: str,
        default_timeframe: str,
        default_indicator: str,
        theme: str,
    ) -> dict:
        if self._session_factory is None:
            existing = self._prefs_memory.get(clerk_user_id)
            now = datetime.now(timezone.utc).isoformat()
            if existing is None:
                row = {
                    "id": str(uuid4()),
                    "clerk_user_id": clerk_user_id,
                    "default_timeframe": default_timeframe,
                    "default_indicator": default_indicator,
                    "theme": theme,
                    "created_at": now,
                    "updated_at": now,
                }
            else:
                row = {
                    **existing,
                    "default_timeframe": default_timeframe,
                    "default_indicator": default_indicator,
                    "theme": theme,
                    "updated_at": now,
                }
            self._prefs_memory[clerk_user_id] = row
            return row
        with self._session_factory() as session:
            row = session.query(UserPreferenceModel).filter(UserPreferenceModel.clerk_user_id == clerk_user_id).first()
            if row is None:
                now = datetime.now(timezone.utc)
                row = UserPreferenceModel(
                    id=str(uuid4()),
                    clerk_user_id=clerk_user_id,
                    default_timeframe=default_timeframe,
                    default_indicator=default_indicator,
                    theme=theme,
                    created_at=now,
                    updated_at=now,
                )
                session.add(row)
            else:
                row.default_timeframe = default_timeframe
                row.default_indicator = default_indicator
                row.theme = theme
                row.updated_at = datetime.now(timezone.utc)
            session.commit()
            return {
                "id": row.id,
                "clerk_user_id": row.clerk_user_id,
                "default_timeframe": row.default_timeframe,
                "default_indicator": row.default_indicator,
                "theme": row.theme,
                "created_at": row.created_at.isoformat(),
                "updated_at": row.updated_at.isoformat(),
            }

    def get_preferences(self, *, clerk_user_id: str) -> dict | None:
        if self._session_factory is None:
            return self._prefs_memory.get(clerk_user_id)
        with self._session_factory() as session:
            row = session.query(UserPreferenceModel).filter(UserPreferenceModel.clerk_user_id == clerk_user_id).first()
            if row is None:
                return None
            return {
                "id": row.id,
                "clerk_user_id": row.clerk_user_id,
                "default_timeframe": row.default_timeframe,
                "default_indicator": row.default_indicator,
                "theme": row.theme,
                "created_at": row.created_at.isoformat(),
                "updated_at": row.updated_at.isoformat(),
            }


user_service = UserService()
