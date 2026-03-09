"""Reporter agent: compile agent outputs into summary reports."""

from __future__ import annotations

from datetime import datetime, timezone

from app.agents.base import AgentContext, AgentResult, BaseAgent


class ReporterAgent(BaseAgent):
    """Generates reports from agent outputs."""

    name = "reporter"

    async def run(self, ctx: AgentContext) -> AgentResult:
        outputs = ctx.outputs
        workflow = ctx.request_payload.get("workflow") or "SCAN"
        report_type = ctx.request_payload.get("report_type") or workflow

        sections: list[str] = []
        sections.append(f"# StrikeEdge Report - {report_type}")
        sections.append(f"\nGenerated: {datetime.now(timezone.utc).isoformat()}")
        sections.append(f"Job ID: {ctx.job_id}")
        sections.append("")

        if "tagger" in outputs:
            t = outputs["tagger"]
            count = t.get("count", 0)
            sections.append(f"## Strike Tagger\nTagged {count} strikes.")
        if "greeks" in outputs:
            g = outputs["greeks"]
            calc = g.get("calculated", 0)
            sections.append(f"## Greeks\nCalculated Greeks for {calc} strikes.")
        if "scanner" in outputs:
            s = outputs["scanner"]
            matched = s.get("matched", [])
            total = s.get("total", 0)
            sections.append(f"## Scanner\nMatched {len(matched)} of {total} strikes.")
            if matched:
                tokens = [m.get("token", "") for m in matched[:20]]
                sections.append("\nTop matches: " + ", ".join(tokens))
        if "backtester" in outputs:
            b = outputs["backtester"]
            sections.append(f"## Backtest\nP&L: {b.get('pnl', 'N/A')}, Sharpe: {b.get('sharpe', 'N/A')}")
        if "analyzer" in outputs:
            a = outputs["analyzer"]
            sections.append(f"## Options Analysis\n{a.get('summary', 'Analysis complete')}")
        if "risk" in outputs:
            r = outputs["risk"]
            sections.append(f"## Risk\nPortfolio Greeks: {r.get('summary', 'Assessment complete')}")

        markdown = "\n".join(sections)
        return AgentResult(
            agent_name=self.name,
            success=True,
            output={
                "markdown": markdown,
                "report_type": report_type,
                "summary": f"Report generated for {report_type}",
            },
        )


reporter_agent = ReporterAgent()
