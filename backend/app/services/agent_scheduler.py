"""Scheduled agent jobs: Researcher every 2h, Sentiment every 30min."""

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING

from apscheduler.schedulers.asyncio import AsyncIOScheduler

if TYPE_CHECKING:
    from app.services.agent_runner import AgentRunnerService


async def _run_researcher_task(agent_runner: "AgentRunnerService") -> None:
    try:
        job = agent_runner.create_job(
            user_id="scheduler",
            job_type="ANALYZE",
            request_payload={"workflow": "ANALYZE", "underlying": "NIFTY", "fetch_news": True},
        )
        await agent_runner.run_job(job["id"])
    except Exception:
        pass


async def _run_sentiment_task(agent_runner: "AgentRunnerService") -> None:
    try:
        job = agent_runner.create_job(
            user_id="scheduler",
            job_type="SENTIMENT",
            request_payload={"workflow": "ANALYZE", "underlying": "NIFTY"},
        )
        await agent_runner.run_job(job["id"])
    except Exception:
        pass


def create_scheduler(agent_runner: "AgentRunnerService") -> AsyncIOScheduler:
    """Create and configure APScheduler for agent jobs."""
    scheduler = AsyncIOScheduler()

    def _trigger_researcher() -> None:
        asyncio.create_task(_run_researcher_task(agent_runner))

    def _trigger_sentiment() -> None:
        asyncio.create_task(_run_sentiment_task(agent_runner))

    scheduler.add_job(_trigger_researcher, "interval", hours=2, id="researcher")
    scheduler.add_job(_trigger_sentiment, "interval", minutes=30, id="sentiment")
    return scheduler
