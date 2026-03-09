"""Sentiment agent: MoneyControl-style scraper, sentiment classification."""

from __future__ import annotations

from app.agents.base import AgentContext, AgentResult, BaseAgent
from app.services.sentiment_scraper import scrape_moneycontrol_headlines
from app.services.ai import ai_service


def _classify_headlines(headlines: list[dict]) -> tuple[str, float]:
    """Simple keyword-based sentiment from headlines. Returns (sentiment, score -1 to 1)."""
    if not headlines:
        return "neutral", 0.0
    bullish = {"surge", "rally", "gain", "rise", "bullish", "positive", "up", "record high"}
    bearish = {"fall", "drop", "decline", "crash", "bearish", "negative", "down", "plunge"}
    scores: list[float] = []
    for h in headlines:
        title = (h.get("title") or "").lower()
        if any(w in title for w in bullish):
            scores.append(0.5)
        elif any(w in title for w in bearish):
            scores.append(-0.5)
        else:
            scores.append(0.0)
    avg = sum(scores) / len(scores) if scores else 0.0
    if avg > 0.2:
        return "bullish", min(1.0, avg + 0.3)
    if avg < -0.2:
        return "bearish", max(-1.0, avg - 0.3)
    return "neutral", avg


class SentimentAgent(BaseAgent):
    """Analyzes news/sentiment. MoneyControl scraper, classification, score aggregation."""

    name = "sentiment"

    async def run(self, ctx: AgentContext) -> AgentResult:
        underlying = ctx.request_payload.get("underlying") or "NIFTY"
        use_ai = bool(ctx.request_payload.get("use_ai_sentiment") or False)

        headlines = scrape_moneycontrol_headlines(underlying=underlying, limit=10)
        sentiment, score = _classify_headlines(headlines)

        if use_ai:
            try:
                ai_sent = ai_service.sentiment(underlying)
                sentiment = ai_sent.get("sentiment", sentiment)
                score = float(ai_sent.get("score", score))
            except Exception:
                pass

        return AgentResult(
            agent_name=self.name,
            success=True,
            output={
                "underlying": underlying,
                "sentiment": sentiment,
                "score": round(score, 4),
                "headlines": headlines[:5],
                "headlines_count": len(headlines),
                "summary": f"Sentiment: {sentiment} (score: {score:.2f}). {len(headlines)} headlines scraped.",
            },
        )


sentiment_agent = SentimentAgent()
