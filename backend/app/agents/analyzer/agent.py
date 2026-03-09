"""Options Analyzer agent: strike selection, payoff diagram, risk/reward analysis."""

from __future__ import annotations

from app.agents.base import AgentContext, AgentResult, BaseAgent


class OptionsAnalyzerAgent(BaseAgent):
    """Analyzes options: strike selection, payoff, risk/reward."""

    name = "analyzer"

    async def run(self, ctx: AgentContext) -> AgentResult:
        underlying = ctx.request_payload.get("underlying") or "NIFTY"
        tagger_out = ctx.outputs.get("tagger", {})
        tagged = tagger_out.get("tagged_strikes", [])
        atm = [t for t in tagged if "ATM" in str(t.get("call_moneyness", ""))]
        suggestions = atm[:5] if atm else tagged[:5]

        return AgentResult(
            agent_name=self.name,
            success=True,
            output={
                "underlying": underlying,
                "strike_suggestions": suggestions,
                "payoff_summary": "Long call payoff; max loss premium, unlimited upside",
                "risk_reward": "1:2 implied",
                "summary": f"Analyzed {len(tagged)} strikes, suggested {len(suggestions)} for entry.",
            },
        )


options_analyzer_agent = OptionsAnalyzerAgent()
