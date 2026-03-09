"""Risk agent: portfolio Greeks sum, VaR, hedging suggestions."""

from __future__ import annotations

from app.agents.base import AgentContext, AgentResult, BaseAgent
from app.services.options_volatility import options_volatility_service


class RiskAgent(BaseAgent):
    """Assesses portfolio risk: Greeks, VaR, hedging."""

    name = "risk"

    async def run(self, ctx: AgentContext) -> AgentResult:
        underlying = ctx.request_payload.get("underlying") or "NIFTY"
        expiry = ctx.request_payload.get("expiry") or ""
        spot = float(ctx.request_payload.get("spot") or 24000.0)
        var_confidence = float(ctx.request_payload.get("var_confidence") or 0.95)

        greeks_out = ctx.outputs.get("greeks", {})
        calculated = greeks_out.get("calculated", 0)

        portfolio_delta = 0.0
        portfolio_gamma = 0.0
        portfolio_theta = 0.0
        portfolio_vega = 0.0
        greeks_count = 0

        try:
            pg = options_volatility_service.portfolio_greeks(
                underlying=underlying,
                expiry=expiry,
            )
            portfolio_delta = pg["delta"]
            portfolio_gamma = pg["gamma"]
            portfolio_theta = pg["theta"]
            portfolio_vega = pg["vega"]
            greeks_count = pg["count"]
        except Exception:
            pass

        var_95 = self._parametric_var(
            delta=portfolio_delta,
            spot=spot,
            volatility=0.18,
            confidence=var_confidence,
        )

        hedges = self._hedging_suggestions(
            delta=portfolio_delta,
            gamma=portfolio_gamma,
            theta=portfolio_theta,
            vega=portfolio_vega,
        )

        return AgentResult(
            agent_name=self.name,
            success=True,
            output={
                "portfolio_delta": portfolio_delta,
                "portfolio_gamma": portfolio_gamma,
                "portfolio_theta": portfolio_theta,
                "portfolio_vega": portfolio_vega,
                "greeks_count": greeks_count,
                "var_95": round(var_95, 2),
                "hedging_suggestions": hedges,
                "summary": f"Portfolio Greeks aggregated ({greeks_count} strikes). VaR({int(var_confidence*100)}): ₹{var_95:.0f}",
            },
        )

    @staticmethod
    def _parametric_var(
        delta: float,
        spot: float,
        volatility: float = 0.18,
        confidence: float = 0.95,
    ) -> float:
        """Parametric VaR: assume normal returns, VaR = |delta| * spot * vol * z."""
        z = 1.65 if confidence >= 0.95 else 1.28 if confidence >= 0.90 else 2.33
        return abs(delta) * spot * (volatility / 100) * z

    @staticmethod
    def _hedging_suggestions(
        delta: float,
        gamma: float,
        theta: float,
        vega: float,
    ) -> list[str]:
        hedges: list[str] = []
        if abs(delta) > 10:
            direction = "short" if delta > 0 else "long"
            hedges.append(f"Delta hedge: Consider {direction} spot/futures (delta={delta:.1f})")
        if abs(gamma) > 0.05:
            hedges.append(f"High gamma ({gamma:.4f}): Portfolio sensitive to spot moves. Consider delta-neutral spread.")
        if theta < -100:
            hedges.append(f"Theta decay ({theta:.0f}/day): Time decay significant. Consider shorter-dated legs or delta hedge.")
        if abs(vega) > 300:
            direction = "long" if vega > 0 else "short"
            hedges.append(f"Vega exposure ({vega:.0f}): Consider {direction} volatility via VIX/options to hedge IV changes.")
        if not hedges:
            hedges.append("Portfolio risk within normal bounds. No immediate hedging recommended.")
        return hedges


risk_agent = RiskAgent()
