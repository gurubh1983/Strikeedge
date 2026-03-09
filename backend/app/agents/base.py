"""Base protocol and utilities for StrikeEdge agents."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any


@dataclass(slots=True)
class AgentContext:
    """Context passed to agents during workflow execution."""

    job_id: str
    user_id: str | None
    workflow_type: str
    request_payload: dict[str, Any]
    outputs: dict[str, Any]


@dataclass(slots=True)
class AgentResult:
    """Result returned by an agent after execution."""

    agent_name: str
    success: bool
    output: dict[str, Any] | None = None
    error: str | None = None


class BaseAgent(ABC):
    """Abstract base for all StrikeEdge agents."""

    name: str = "base"

    @abstractmethod
    async def run(self, ctx: AgentContext) -> AgentResult:
        """Execute agent logic. Subclasses must implement."""
        ...
