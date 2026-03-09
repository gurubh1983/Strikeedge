from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy.orm import Session, sessionmaker

from app.db.models import ScanJobModel, ScanResultModel
from app.schemas import ScanResultOut


class ScanStoreService:
    def __init__(self) -> None:
        self._session_factory: sessionmaker[Session] | None = None
        self._memory: dict[str, dict] = {}

    def set_session_factory(self, session_factory: sessionmaker[Session]) -> None:
        self._session_factory = session_factory

    def save_scan(self, timeframe: str, rules: list[dict], results: list[ScanResultOut]) -> str:
        scan_id = str(uuid4())
        payload = [item.model_dump() for item in results]
        if self._session_factory is None:
            self._memory[scan_id] = {
                "scan_id": scan_id,
                "timeframe": timeframe,
                "rules": rules,
                "results": payload,
                "status": "completed",
                "created_at": datetime.now(timezone.utc).isoformat(),
            }
            return scan_id

        with self._session_factory() as session:
            session.add(
                ScanJobModel(
                    id=scan_id,
                    timeframe=timeframe,
                    rules=rules,
                    results=payload,
                    status="completed",
                    created_at=datetime.now(timezone.utc),
                )
            )
            for item in payload:
                session.add(
                    ScanResultModel(
                        scan_id=scan_id,
                        token=item["token"],
                        matched=1 if item["matched"] else 0,
                        reason=item["reason"],
                        created_at=datetime.now(timezone.utc),
                    )
                )
            session.commit()
        return scan_id

    def get_scan(self, scan_id: str) -> dict | None:
        if self._session_factory is None:
            row = self._memory.get(scan_id)
            if row is None:
                return None
            return {"scan_id": row["scan_id"], "status": row["status"], "results": row["results"]}

        with self._session_factory() as session:
            row = session.get(ScanJobModel, scan_id)
            if row is None:
                return None
            result_rows = (
                session.query(ScanResultModel)
                .filter(ScanResultModel.scan_id == scan_id)
                .order_by(ScanResultModel.created_at.asc())
                .all()
            )
            results = [
                {"token": item.token, "matched": bool(item.matched), "reason": item.reason}
                for item in result_rows
            ] or row.results
            return {"scan_id": row.id, "status": row.status, "results": results}


scan_store_service = ScanStoreService()
