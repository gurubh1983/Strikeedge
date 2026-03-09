"""Researcher agent: market intelligence, FII/DII, unusual OI detection."""

from __future__ import annotations

from app.agents.base import AgentContext, AgentResult, BaseAgent
from app.services.research import fetch_fii_dii, fetch_news_api
from app.services.options_volatility import options_volatility_service


def _store_to_chroma(insights: list[dict]) -> None:
    """Optionally store insights to ChromaDB if available."""
    try:
        import chromadb
        from uuid import uuid4
        client = chromadb.Client(chromadb.config.Settings(anonymized_telemetry=False))
        coll = client.get_or_create_collection("strikeedge_research", metadata={"hnsw:space": "cosine"})
        texts = [str(i) for i in insights[:20]]
        if texts:
            coll.add(ids=[f"r_{uuid4().hex[:12]}" for _ in texts], documents=texts)
    except Exception:
        pass


class ResearcherAgent(BaseAgent):
    """Gathers market intelligence. Web scraping, News API, FII/DII, unusual OI."""

    name = "researcher"

    async def run(self, ctx: AgentContext) -> AgentResult:
        underlying = ctx.request_payload.get("underlying") or "NIFTY"
        expiry = ctx.request_payload.get("expiry") or ""
        fetch_news = bool(ctx.request_payload.get("fetch_news") or True)
        insights: list[dict] = []

        fii_dii = fetch_fii_dii()
        if fii_dii:
            insights.extend(fii_dii)

        if fetch_news:
            news = fetch_news_api(query=f"{underlying} options market", limit=5)
            insights.extend(news)

        try:
            if options_volatility_service._session_factory:
                spikes = options_volatility_service.oi_spikes(
                    underlying=underlying,
                    expiry=expiry,
                    threshold_pct=20.0,
                    limit=20,
                )
                insights.extend([{"type": "oi_spike", "data": s} for s in spikes])
        except Exception:
            pass

        _store_to_chroma(insights)

        return AgentResult(
            agent_name=self.name,
            success=True,
            output={"insights": insights, "underlying": underlying},
        )


researcher_agent = ResearcherAgent()
