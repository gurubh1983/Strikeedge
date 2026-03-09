"""Workflow definitions: SCAN, BACKTEST, ANALYZE."""

from __future__ import annotations

from app.agents.orchestrator.agent import WorkflowDef, WorkflowRegistry, WorkflowStep
from app.agents.tagger.agent import strike_tagger_agent
from app.agents.greeks.agent import greeks_agent
from app.agents.scanner.agent import signal_scanner_agent
from app.agents.reporter.agent import reporter_agent
from app.agents.researcher.agent import researcher_agent
from app.agents.sentiment.agent import sentiment_agent
from app.agents.backtester.agent import backtester_agent
from app.agents.optimizer.agent import optimizer_agent
from app.agents.analyzer.agent import options_analyzer_agent
from app.agents.risk.agent import risk_agent


async def _invoke(agent, ctx):
    return await agent.run(ctx)


def _step(name: str, agent):
    return WorkflowStep(agent_name=name, invoke=lambda ctx: _invoke(agent, ctx))


def register_workflows(registry: WorkflowRegistry) -> None:
    """Register SCAN, BACKTEST, ANALYZE workflows and agents."""
    registry.register_agent("tagger", lambda ctx: _invoke(strike_tagger_agent, ctx))
    registry.register_agent("greeks", lambda ctx: _invoke(greeks_agent, ctx))
    registry.register_agent("scanner", lambda ctx: _invoke(signal_scanner_agent, ctx))
    registry.register_agent("reporter", lambda ctx: _invoke(reporter_agent, ctx))
    registry.register_agent("researcher", lambda ctx: _invoke(researcher_agent, ctx))
    registry.register_agent("sentiment", lambda ctx: _invoke(sentiment_agent, ctx))
    registry.register_agent("backtester", lambda ctx: _invoke(backtester_agent, ctx))
    registry.register_agent("optimizer", lambda ctx: _invoke(optimizer_agent, ctx))
    registry.register_agent("analyzer", lambda ctx: _invoke(options_analyzer_agent, ctx))
    registry.register_agent("risk", lambda ctx: _invoke(risk_agent, ctx))

    registry.register_workflow(
        "SCAN",
        WorkflowDef(
            name="SCAN",
            description="Tag strikes, scan for signals, generate report",
            steps=[
                _step("tagger", strike_tagger_agent),
                _step("greeks", greeks_agent),
                _step("scanner", signal_scanner_agent),
                _step("reporter", reporter_agent),
            ],
        ),
    )
    registry.register_workflow(
        "BACKTEST",
        WorkflowDef(
            name="BACKTEST",
            description="Scan, backtest, optimize, report",
            steps=[
                _step("tagger", strike_tagger_agent),
                _step("scanner", signal_scanner_agent),
                _step("backtester", backtester_agent),
                _step("optimizer", optimizer_agent),
                _step("reporter", reporter_agent),
            ],
        ),
    )
    registry.register_workflow(
        "ANALYZE",
        WorkflowDef(
            name="ANALYZE",
            description="Research, Greeks, Risk, Analyze, Report",
            steps=[
                [
                    _step("researcher", researcher_agent),
                    _step("greeks", greeks_agent),
                    _step("sentiment", sentiment_agent),
                    _step("risk", risk_agent),
                ],
                _step("tagger", strike_tagger_agent),
                _step("analyzer", options_analyzer_agent),
                _step("reporter", reporter_agent),
            ],
        ),
    )
