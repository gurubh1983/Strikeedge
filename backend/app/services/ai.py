from __future__ import annotations

from app.schemas import AiInsight, PatternOut, PatternSignalOut, SentimentOut


class AIInsightService:
    def generate(self, symbol: str) -> AiInsight:
        sym = symbol.upper()
        return AiInsight(
            thesis=f"{sym} shows constructive momentum with controlled risk.",
            confidence=0.78,
            factors=[
                {"factor": "RSI momentum", "direction": "bullish", "weight": 0.35, "explanation": "RSI above threshold"},
                {"factor": "Trend quality", "direction": "bullish", "weight": 0.25, "explanation": "Trend remains intact"},
            ],
            risk_flags=["Event risk", "Intraday volatility expansion"],
            sources=[
                {"source_type": "derived_indicator", "source_id": f"{sym}:rsi_14", "label": "RSI 14"},
                {"source_type": "model_inference", "source_id": f"{sym}:ensemble_v1", "label": "Ensemble model"},
            ],
        )

    def sentiment(self, symbol: str) -> SentimentOut:
        sym = symbol.upper()
        seed = sum(ord(c) for c in sym) % 100
        score = round((seed - 50) / 50, 3)
        if score > 0.2:
            sentiment = "bullish"
        elif score < -0.2:
            sentiment = "bearish"
        else:
            sentiment = "neutral"
        return SentimentOut(
            symbol=sym,
            sentiment=sentiment,
            score=score,
            summary=f"{sym} sentiment model indicates {sentiment} bias.",
        )

    def detect_patterns(self, symbol: str, timeframe: str = "5m") -> PatternOut:
        sym = symbol.upper()
        return PatternOut(
            symbol=sym,
            timeframe=timeframe,
            signals=[
                PatternSignalOut(
                    pattern="Bullish Engulfing",
                    direction="bullish",
                    confidence=0.72,
                    description="Recent candle sequence suggests potential reversal to upside.",
                ),
                PatternSignalOut(
                    pattern="Range Compression",
                    direction="neutral",
                    confidence=0.61,
                    description="Volatility compression may precede directional breakout.",
                ),
            ],
        )


ai_service = AIInsightService()
