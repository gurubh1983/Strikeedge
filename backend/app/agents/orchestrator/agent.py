"""Orchestrator agent: coordinates workflows and specialist agents."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Callable, Awaitable
from uuid import uuid4

from app.agents.base import AgentContext, AgentResult, BaseAgent


@dataclass
class WorkflowStep:
    """Single step in a workflow - invokes an agent."""

    agent_name: str
    invoke: Callable[[AgentContext], Awaitable[AgentResult]]


@dataclass
class WorkflowDef:
    """Workflow definition: name, steps, and whether steps run in parallel."""

    name: str
    steps: list[WorkflowStep | list[WorkflowStep]]  # list = parallel group
    description: str = ""


class WorkflowRegistry:
    """Registry of available workflows (SCAN, BACKTEST, ANALYZE, etc.)."""

    def __init__(self) -> None:
        self._workflows: dict[str, WorkflowDef] = {}
        self._agents: dict[str, Callable[[AgentContext], Awaitable[AgentResult]]] = {}

    def register_agent(self, name: str, invoke: Callable[[AgentContext], Awaitable[AgentResult]]) -> None:
        self._agents[name] = invoke

    def register_workflow(self, workflow_id: str, definition: WorkflowDef) -> None:
        self._workflows[workflow_id] = definition

    def get_workflow(self, workflow_id: str) -> WorkflowDef | None:
        return self._workflows.get(workflow_id)

    def get_agent(self, name: str) -> Callable[[AgentContext], Awaitable[AgentResult]] | None:
        return self._agents.get(name)


WORKFLOW_REGISTRY = WorkflowRegistry()


class OrchestratorAgent(BaseAgent):
    """Conductor agent that manages workflows and invokes specialist agents."""

    name = "orchestrator"

    def __init__(self, registry: WorkflowRegistry | None = None) -> None:
        self.registry = registry or WORKFLOW_REGISTRY

    async def run(self, ctx: AgentContext) -> AgentResult:
        """Execute the workflow specified in request_payload."""
        workflow_id = ctx.request_payload.get("workflow") or "SCAN"
        workflow = self.registry.get_workflow(workflow_id)
        if workflow is None:
            return AgentResult(
                agent_name=self.name,
                success=False,
                error=f"Unknown workflow: {workflow_id}",
            )
        outputs: dict[str, Any] = dict(ctx.outputs)
        errors: list[str] = []
        try:
            for step in workflow.steps:
                if isinstance(step, list):
                    results = await asyncio.gather(
                        *[self._run_step(s, ctx, outputs) for s in step],
                        return_exceptions=True,
                    )
                    for r in results:
                        if isinstance(r, BaseException):
                            errors.append(str(r))
                        elif isinstance(r, AgentResult):
                            if r.success and r.output:
                                outputs[r.agent_name] = r.output
                            elif not r.success and r.error:
                                errors.append(r.error)
                else:
                    result = await self._run_step(step, ctx, outputs)
                    if result.success and result.output:
                        outputs[result.agent_name] = result.output
                    elif not result.success and result.error:
                        errors.append(result.error)
            return AgentResult(
                agent_name=self.name,
                success=len(errors) == 0,
                output={"outputs": outputs, "errors": errors},
                error="; ".join(errors) if errors else None,
            )
        except Exception as exc:
            return AgentResult(
                agent_name=self.name,
                success=False,
                output={"outputs": outputs},
                error=str(exc),
            )

    async def _run_step(
        self,
        step: WorkflowStep,
        ctx: AgentContext,
        outputs: dict[str, Any],
    ) -> AgentResult:
        sub_ctx = AgentContext(
            job_id=ctx.job_id,
            user_id=ctx.user_id,
            workflow_type=ctx.workflow_type,
            request_payload=ctx.request_payload,
            outputs=dict(outputs),
        )
        return await step.invoke(sub_ctx)


orchestrator_agent = OrchestratorAgent()
