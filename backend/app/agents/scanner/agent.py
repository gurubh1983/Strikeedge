"""Signal Scanner agent: batch processing, parallel indicator calc, filter conditions."""

from __future__ import annotations

from app.agents.base import AgentContext, AgentResult, BaseAgent
from app.screener.scanner import ConditionGroup, IndicatorCondition, evaluate_group
from app.services.market_data import market_data_service


class SignalScannerAgent(BaseAgent):
    """Scans strikes against screener conditions, batch processing."""

    name = "scanner"

    async def run(self, ctx: AgentContext) -> AgentResult:
        timeframe = ctx.request_payload.get("timeframe") or "5m"
        underlying = ctx.request_payload.get("underlying")
        rules = ctx.request_payload.get("rules") or []
        groups_raw = ctx.request_payload.get("groups") or []
        limit = int(ctx.request_payload.get("limit") or 500)

        if groups_raw:
            groups = [
                ConditionGroup(
                    logical_operator=g.get("logical_operator", "AND"),
                    conditions=[
                        IndicatorCondition(field=r["field"], operator=r["operator"], value=float(r["value"]))
                        for r in g.get("rules", [])
                    ],
                )
                for g in groups_raw
            ]
        elif rules:
            groups = [
                ConditionGroup(
                    logical_operator="AND",
                    conditions=[
                        IndicatorCondition(field=r["field"], operator=r["operator"], value=float(r["value"]))
                        for r in rules
                    ],
                )
            ]
        else:
            groups = []

        rows, previous_rows = market_data_service.latest_and_previous_indicator_rows(timeframe=timeframe)
        if not rows:
            return AgentResult(
                agent_name=self.name,
                success=True,
                output={"matched": [], "total": 0, "matched_count": 0},
            )
        if underlying:
            prefix = underlying.upper()
            rows = [r for r in rows if str(r.get("token", "")).startswith(prefix)]
        rows = rows[:limit]

        previous_map = previous_rows if isinstance(previous_rows, dict) else {}

        matched: list[dict] = []
        for row in rows:
            token = str(row.get("token", ""))
            prev = previous_map.get(token)
            ok = True
            for group in groups:
                if not evaluate_group(row, prev, group):
                    ok = False
                    break
            if ok and groups:
                matched.append({"token": token, "reason": "rules satisfied"})
            elif not groups:
                matched.append({"token": token, "reason": "no filters"})

        return AgentResult(
            agent_name=self.name,
            success=True,
            output={"matched": matched, "total": len(rows), "matched_count": len(matched)},
        )


signal_scanner_agent = SignalScannerAgent()
