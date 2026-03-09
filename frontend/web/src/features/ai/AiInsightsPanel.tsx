type Insight = {
  thesis: string;
  confidence: number;
  riskFlags: string[];
};

export function AiInsightsPanel({ insight }: { insight: Insight }) {
  return (
    <section className="rounded-xl border border-slate-700 bg-slate-900 p-4">
      <h2 className="text-lg font-semibold text-slate-100">AI Insight</h2>
      <p className="mt-2 text-sm text-slate-300">{insight.thesis}</p>
      <p className="mt-1 text-xs text-slate-400">Confidence: {(insight.confidence * 100).toFixed(0)}%</p>
      <ul className="mt-3 list-disc pl-5 text-xs text-amber-300">
        {insight.riskFlags.map((flag) => (
          <li key={flag}>{flag}</li>
        ))}
      </ul>
    </section>
  );
}
