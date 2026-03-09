"use client";

import { useCallback, useEffect, useState } from "react";

import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { fetchAiInsights, fetchAiPatterns, fetchAiSentiment, type AiInsightPayload, type AiSentimentPayload, type PatternPayload } from "@/lib/api/client";

export default function AiInsightsPage() {
  const [symbol, setSymbol] = useState("NIFTY");
  const [insight, setInsight] = useState<AiInsightPayload | null>(null);
  const [sentiment, setSentiment] = useState<AiSentimentPayload | null>(null);
  const [patterns, setPatterns] = useState<PatternPayload | null>(null);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    try {
      setError(null);
      const [i, s, p] = await Promise.all([fetchAiInsights(symbol), fetchAiSentiment(symbol), fetchAiPatterns(symbol)]);
      setInsight(i);
      setSentiment(s);
      setPatterns(p);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load AI analytics");
    }
  }, [symbol]);

  useEffect(() => {
    void load();
  }, [load]);

  return (
    <section className="space-y-4">
      <Card>
        <h2 className="mb-3 text-lg font-semibold text-slate-100">AI Insights</h2>
        <div className="flex gap-2">
          <Input value={symbol} onChange={(e) => setSymbol(e.target.value.toUpperCase())} />
          <Button onClick={() => void load()}>Load</Button>
        </div>
        {error ? <p className="mt-2 text-sm text-rose-400">{error}</p> : null}
      </Card>

      {insight ? (
        <Card>
          <h3 className="text-sm font-semibold text-slate-100">Thesis</h3>
          <p className="mt-2 text-sm text-slate-300">{insight.thesis}</p>
          <p className="mt-1 text-xs text-slate-400">Confidence: {(insight.confidence * 100).toFixed(0)}%</p>
        </Card>
      ) : null}

      {sentiment ? (
        <Card>
          <h3 className="text-sm font-semibold text-slate-100">Sentiment</h3>
          <p className="mt-2 text-sm text-slate-300">
            {sentiment.sentiment.toUpperCase()} ({sentiment.score})
          </p>
          <p className="mt-1 text-xs text-slate-400">{sentiment.summary}</p>
        </Card>
      ) : null}

      {patterns ? (
        <Card>
          <h3 className="text-sm font-semibold text-slate-100">Pattern Signals</h3>
          <ul className="mt-2 space-y-2 text-sm text-slate-300">
            {patterns.signals.map((signal) => (
              <li key={signal.pattern} className="rounded border border-slate-800 p-2">
                <p className="font-medium text-slate-200">
                  {signal.pattern} - {signal.direction}
                </p>
                <p className="text-xs text-slate-400">{signal.description}</p>
              </li>
            ))}
          </ul>
        </Card>
      ) : null}
    </section>
  );
}
