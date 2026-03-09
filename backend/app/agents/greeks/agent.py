"""Greeks agent: IV, Delta, Gamma, Theta, Vega calculations and persistence."""

from __future__ import annotations

from app.agents.base import AgentContext, AgentResult, BaseAgent


class GreeksAgent(BaseAgent):
    """Calculates and stores Greeks for option strikes."""

    name = "greeks"

    async def run(self, ctx: AgentContext) -> AgentResult:
        underlying = ctx.request_payload.get("underlying") or "NIFTY"
        expiry = ctx.request_payload.get("expiry") or ""
        spot = float(ctx.request_payload.get("spot") or 24000.0)
        time_to_expiry_years = float(ctx.request_payload.get("time_to_expiry_years") or 0.08)
        risk_free_rate = float(ctx.request_payload.get("risk_free_rate") or 0.06)

        calculated = 0
        try:
            from app.services.options_volatility import options_volatility_service
            calculated = options_volatility_service.calculate_greeks_for_chain(
                underlying=underlying,
                expiry=expiry,
                spot=spot,
                time_to_expiry_years=time_to_expiry_years,
                risk_free_rate=risk_free_rate,
            )
        except Exception as e:
            return AgentResult(
                agent_name=self.name,
                success=False,
                output={"calculated": 0},
                error=str(e),
            )
        return AgentResult(
            agent_name=self.name,
            success=True,
            output={"calculated": calculated, "underlying": underlying, "expiry": expiry},
        )


greeks_agent = GreeksAgent()
