import { useState } from "react";

export function StrategyBuilder() {
  const [name, setName] = useState("Momentum Strategy");
  return (
    <section className="rounded-xl border border-slate-700 bg-slate-900 p-4">
      <h2 className="text-lg font-semibold text-slate-100">Strategy Builder</h2>
      <p className="mt-1 text-sm text-slate-400">Enterprise rule-builder foundation for IF/AND/OR strategy composition.</p>
      <input
        className="mt-3 w-full rounded border border-slate-700 bg-slate-950 px-3 py-2 text-slate-100"
        value={name}
        onChange={(event) => setName(event.target.value)}
      />
    </section>
  );
}
