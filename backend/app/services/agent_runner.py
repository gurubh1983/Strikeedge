"""Agent job runner: creates jobs, runs orchestrator, updates status."""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy.orm import Session, sessionmaker

from app.agents.base import AgentContext
from app.agents.orchestrator.agent import WORKFLOW_REGISTRY, orchestrator_agent
from app.agents.workflows import register_workflows
from app.db.models import AgentJobModel


def _ensure_workflows_registered() -> None:
    if not WORKFLOW_REGISTRY.get_workflow("SCAN"):
        register_workflows(WORKFLOW_REGISTRY)


class AgentRunnerService:
    def __init__(self) -> None:
        self._session_factory: sessionmaker[Session] | None = None
        self._memory_jobs: dict[str, dict] = {}

    def set_session_factory(self, session_factory: sessionmaker[Session]) -> None:
        self._session_factory = session_factory

    def create_job(self, *, user_id: str, job_type: str, request_payload: dict) -> dict:
        _ensure_workflows_registered()
        job_id = str(uuid4())
        row = {
            "id": job_id,
            "user_id": user_id,
            "job_type": job_type,
            "status": "pending",
            "request_payload": request_payload,
            "output_payload": None,
            "error_message": None,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        if self._session_factory:
            with self._session_factory() as session:
                session.add(
                    AgentJobModel(
                        id=job_id,
                        user_id=user_id,
                        job_type=job_type,
                        status="pending",
                        request_payload=request_payload,
                        output_payload=None,
                        error_message=None,
                        created_at=datetime.now(timezone.utc),
                    )
                )
                session.commit()
        else:
            self._memory_jobs[job_id] = row
        return {"id": job_id, "status": "pending", "job_type": job_type}

    async def run_job(self, job_id: str) -> dict | None:
        _ensure_workflows_registered()
        user_id = ""
        request_payload = {}
        if self._session_factory:
            with self._session_factory() as session:
                row = session.get(AgentJobModel, job_id)
                if row is None:
                    mem = self._memory_jobs.get(job_id)
                    if mem is None:
                        return None
                    user_id = mem["user_id"]
                    request_payload = dict(mem["request_payload"])
                else:
                    user_id = row.user_id
                    request_payload = dict(row.request_payload)
                    row.status = "running"
                    session.commit()
        else:
            mem = self._memory_jobs.get(job_id)
            if mem is None:
                return None
            user_id = mem["user_id"]
            request_payload = dict(mem["request_payload"])
            mem["status"] = "running"

        workflow = request_payload.get("workflow") or "SCAN"
        ctx = AgentContext(
            job_id=job_id,
            user_id=user_id,
            workflow_type=workflow,
            request_payload=request_payload,
            outputs={},
        )
        result = await orchestrator_agent.run(ctx)

        if self._session_factory:
            with self._session_factory() as session:
                row = session.get(AgentJobModel, job_id)
                if row:
                    row.status = "completed" if result.success else "failed"
                    row.output_payload = result.output
                    row.error_message = result.error
                    session.commit()
        else:
            mem = self._memory_jobs.get(job_id)
            if mem:
                mem["status"] = "completed" if result.success else "failed"
                mem["output_payload"] = result.output
                mem["error_message"] = result.error

        return {
            "id": job_id,
            "status": "completed" if result.success else "failed",
            "output": result.output,
            "error": result.error,
        }

    def get_job(self, job_id: str) -> dict | None:
        if self._session_factory:
            with self._session_factory() as session:
                row = session.get(AgentJobModel, job_id)
                if row is not None:
                    return {
                        "id": row.id,
                        "user_id": row.user_id,
                        "job_type": row.job_type,
                        "status": row.status,
                        "request_payload": row.request_payload,
                        "output_payload": row.output_payload,
                        "error_message": row.error_message,
                        "created_at": row.created_at.isoformat(),
                    }
        mem = self._memory_jobs.get(job_id)
        if mem is not None:
            return dict(mem)
        return None


agent_runner_service = AgentRunnerService()
