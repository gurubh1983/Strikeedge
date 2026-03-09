from __future__ import annotations

import base64
import json
from datetime import datetime, timezone
from uuid import uuid4

from fastapi import HTTPException, status

from app.core.logging import get_logger, log_event
from app.core.metrics import metrics_registry
from app.persistence.read_models import AlertReadModel, AuditEventReadModel, StrategyReadModel, WorkspaceReadModel
from app.repositories.base import MutableStore
from app.repositories.memory import InMemoryStore
from app.schemas import AlertIn, StrategyIn, WorkspaceIn

logger = get_logger("strikeedge.strategy")


class StrategyService:
    def __init__(self, store: MutableStore | None = None) -> None:
        self.store: MutableStore = store or InMemoryStore()

    def set_store(self, store: MutableStore) -> None:
        self.store = store

    def create_strategy(self, payload: StrategyIn, actor_id: str) -> dict:
        self._validate_strategy(payload)
        strategy = {
            "id": str(uuid4()),
            "owner_id": payload.user_id,
            "name": payload.name,
            "rules": [r.model_dump() for r in payload.rules],
        }
        strategy = self.store.create("strategies", strategy)
        self._audit("strategy", strategy["id"], "created", actor_id, strategy)
        log_event(
            logger,
            "strategy_created",
            strategy_id=strategy["id"],
            owner_id=strategy["owner_id"],
            actor_id=actor_id,
        )
        metrics_registry.incr("service_strategy_create_total")
        return StrategyReadModel.model_validate(strategy).model_dump(mode="json")

    def create_workspace(self, payload: WorkspaceIn, actor_id: str) -> dict:
        self._validate_workspace(payload)
        workspace = {
            "id": str(uuid4()),
            "owner_id": payload.user_id,
            "name": payload.name,
            "layout": payload.layout,
        }
        workspace = self.store.create("workspaces", workspace)
        self._audit("workspace", workspace["id"], "created", actor_id, workspace)
        log_event(
            logger,
            "workspace_created",
            workspace_id=workspace["id"],
            owner_id=workspace["owner_id"],
            actor_id=actor_id,
        )
        metrics_registry.incr("service_workspace_create_total")
        return WorkspaceReadModel.model_validate(workspace).model_dump(mode="json")

    def create_alert(self, payload: AlertIn, actor_id: str) -> dict:
        self._validate_alert(payload)
        alert = {
            "id": str(uuid4()),
            "user_id": payload.user_id,
            "name": payload.name,
            "rule": payload.rule.model_dump(),
        }
        alert = self.store.create("alerts", alert)
        self._audit("alert", alert["id"], "created", actor_id, alert)
        log_event(
            logger,
            "alert_created",
            alert_id=alert["id"],
            user_id=alert["user_id"],
            actor_id=actor_id,
        )
        metrics_registry.incr("service_alert_create_total")
        return AlertReadModel.model_validate(alert).model_dump(mode="json")

    def list_alerts(
        self,
        user_id: str | None = None,
        limit: int = 50,
        offset: int = 0,
        sort_by: str = "created_at",
        sort_order: str = "desc",
    ) -> list[dict]:
        rows = self.store.list("alerts", filters={"user_id": user_id})
        rows = self._sorted(rows, sort_by=sort_by, sort_order=sort_order)
        paged = rows[offset : offset + limit]
        metrics_registry.incr("service_alert_list_total")
        return [AlertReadModel.model_validate(row).model_dump(mode="json") for row in paged]

    def list_audit(
        self,
        actor_id: str | None = None,
        entity_type: str | None = None,
        limit: int = 100,
        offset: int = 0,
        sort_by: str = "created_at",
        sort_order: str = "desc",
    ) -> list[dict]:
        rows = self.store.list("audit", filters={"actor_id": actor_id, "entity_type": entity_type})
        rows = self._sorted(rows, sort_by=sort_by, sort_order=sort_order)
        paged = rows[offset : offset + limit]
        metrics_registry.incr("service_audit_list_total")
        return [AuditEventReadModel.model_validate(row).model_dump(mode="json") for row in paged]

    def list_alerts_cursor(
        self,
        user_id: str | None = None,
        limit: int = 50,
        cursor: str | None = None,
        sort_by: str = "created_at",
        sort_order: str = "desc",
    ) -> dict:
        rows = self.store.list("alerts", filters={"user_id": user_id})
        rows = self._sorted(rows, sort_by=sort_by, sort_order=sort_order)
        page_rows, next_cursor = self._cursor_page(rows, limit=limit, cursor=cursor)
        metrics_registry.incr("service_alert_cursor_list_total")
        return {
            "items": [AlertReadModel.model_validate(row).model_dump(mode="json") for row in page_rows],
            "next_cursor": next_cursor,
        }

    def list_audit_cursor(
        self,
        actor_id: str | None = None,
        entity_type: str | None = None,
        limit: int = 100,
        cursor: str | None = None,
        sort_by: str = "created_at",
        sort_order: str = "desc",
    ) -> dict:
        rows = self.store.list("audit", filters={"actor_id": actor_id, "entity_type": entity_type})
        rows = self._sorted(rows, sort_by=sort_by, sort_order=sort_order)
        page_rows, next_cursor = self._cursor_page(rows, limit=limit, cursor=cursor)
        metrics_registry.incr("service_audit_cursor_list_total")
        return {
            "items": [AuditEventReadModel.model_validate(row).model_dump(mode="json") for row in page_rows],
            "next_cursor": next_cursor,
        }

    def _audit(self, entity_type: str, entity_id: str, action: str, actor_id: str, payload: dict) -> None:
        self.store.create(
            "audit",
            {
                "id": str(uuid4()),
                "entity_type": entity_type,
                "entity_id": entity_id,
                "action": action,
                "actor_id": actor_id,
                "payload": payload,
                "created_at": datetime.now(timezone.utc),
            },
        )

    @staticmethod
    def _validate_strategy(payload: StrategyIn) -> None:
        if not payload.name.strip():
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail="Strategy name cannot be empty")
        if not payload.rules:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail="At least one strategy rule is required")
        if len(payload.rules) > 20:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail="Too many strategy rules (max 20)")
        for rule in payload.rules:
            if rule.field == "rsi_14" and not (0 <= rule.value <= 100):
                raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail="RSI rule value must be between 0 and 100")

    @staticmethod
    def _validate_workspace(payload: WorkspaceIn) -> None:
        if not payload.name.strip():
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail="Workspace name cannot be empty")

    @staticmethod
    def _validate_alert(payload: AlertIn) -> None:
        if not payload.name.strip():
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail="Alert name cannot be empty")
        if payload.rule.field == "rsi_14" and not (0 <= payload.rule.value <= 100):
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail="RSI alert value must be between 0 and 100")

    @staticmethod
    def _sorted(rows: list[dict], *, sort_by: str, sort_order: str) -> list[dict]:
        reverse = sort_order.lower() == "desc"
        if sort_by not in {"created_at", "name", "id", "actor_id", "user_id", "owner_id", "entity_type"}:
            sort_by = "created_at"
        return sorted(rows, key=lambda row: str(row.get(sort_by, "")), reverse=reverse)

    @staticmethod
    def _cursor_page(rows: list[dict], *, limit: int, cursor: str | None) -> tuple[list[dict], str | None]:
        start = 0
        if cursor:
            try:
                payload = json.loads(base64.urlsafe_b64decode(cursor.encode()).decode())
                last_id = payload.get("last_id")
                if isinstance(last_id, str):
                    for idx, row in enumerate(rows):
                        if row.get("id") == last_id:
                            start = idx + 1
                            break
            except Exception:
                start = 0
        page = rows[start : start + limit]
        if not page:
            return [], None
        last_id = page[-1].get("id")
        if not isinstance(last_id, str):
            return page, None
        next_cursor = base64.urlsafe_b64encode(json.dumps({"last_id": last_id}).encode()).decode()
        return page, next_cursor


strategy_service = StrategyService()
