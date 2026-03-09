"""Strike Tagger agent: classify strikes with moneyness and liquidity."""

from __future__ import annotations

from typing import Literal

from app.agents.base import AgentContext, AgentResult, BaseAgent


def derive_moneyness(spot: float, strike: float, option_type: str) -> Literal["ITM", "ATM", "OTM", "Deep ITM", "Deep OTM"]:
    """Classify strike by moneyness (5% bands for ATM)."""
    if spot <= 0:
        return "ATM"
    pct = abs(strike - spot) / spot * 100.0
    is_call = option_type.upper() in {"CE", "C"}
    if pct <= 2.5:
        return "ATM"
    if is_call:
        if strike < spot:
            return "Deep ITM" if pct > 10 else "ITM"
        return "Deep OTM" if pct > 10 else "OTM"
    if strike > spot:
        return "Deep ITM" if pct > 10 else "ITM"
    return "Deep OTM" if pct > 10 else "OTM"


def liquidity_score(oi: int, volume: int, oi_threshold: int = 1000) -> float:
    """Liquidity score 0-1 based on OI and volume."""
    if oi_threshold <= 0:
        return 1.0
    oi_factor = min(1.0, oi / (oi_threshold * 10))
    vol_factor = min(1.0, volume / max(1, oi) * 2)
    return round((oi_factor * 0.6 + vol_factor * 0.4), 3)


class StrikeTaggerAgent(BaseAgent):
    """Classifies and enriches strike metadata: moneyness, liquidity."""

    name = "tagger"

    async def run(self, ctx: AgentContext) -> AgentResult:
        underlyings = ctx.request_payload.get("underlyings") or ["NIFTY"]
        expiry = ctx.request_payload.get("expiry") or ""
        spot = ctx.request_payload.get("spot") or 24000.0

        tagged: list[dict] = []
        chain = ctx.outputs.get("options_chain") or ctx.request_payload.get("options_chain") or []
        if not chain:
            try:
                from app.services.options_chain import options_chain_service
                for underlying in underlyings:
                    rows = options_chain_service.get_chain(underlying=underlying, expiry=expiry, limit=200)
                    chain.extend([{**dict(r), "underlying": underlying} for r in rows] if rows else [])
            except Exception:
                pass
        for row in chain:
            underlying = str(row.get("underlying") or (underlyings[0] if underlyings else "NIFTY"))
            strike_price = float(row.get("strike_price") or 0)
            call_oi = int(row.get("call_oi") or 0)
            put_oi = int(row.get("put_oi") or 0)
            total_oi = call_oi + put_oi
            call_token = row.get("call_token") or row.get("call_symbol") or ""
            put_token = row.get("put_token") or row.get("put_symbol") or ""
            liq = liquidity_score(total_oi, total_oi // 4)
            tagged.append({
                "token": call_token or put_token,
                "strike_price": strike_price,
                "underlying": underlying,
                "call_moneyness": derive_moneyness(spot, strike_price, "CE"),
                "put_moneyness": derive_moneyness(spot, strike_price, "PE"),
                "liquidity_score": liq,
                "call_oi": call_oi,
                "put_oi": put_oi,
            })
        return AgentResult(
            agent_name=self.name,
            success=True,
            output={"tagged_strikes": tagged, "count": len(tagged)},
        )


strike_tagger_agent = StrikeTaggerAgent()
