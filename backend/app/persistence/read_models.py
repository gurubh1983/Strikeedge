from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel


class StrategyReadModel(BaseModel):
    id: str
    owner_id: str
    name: str
    rules: list[dict[str, Any]]
    created_at: datetime | str | None = None


class WorkspaceReadModel(BaseModel):
    id: str
    owner_id: str
    name: str
    layout: dict[str, Any]
    created_at: datetime | str | None = None


class AlertReadModel(BaseModel):
    id: str
    user_id: str
    name: str
    rule: dict[str, Any]
    created_at: datetime | str | None = None


class AuditEventReadModel(BaseModel):
    id: str
    entity_type: str
    entity_id: str
    action: str
    actor_id: str
    payload: dict[str, Any]
    created_at: datetime | str | None = None
