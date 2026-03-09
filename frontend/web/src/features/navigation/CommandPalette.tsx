import { useMemo, useState } from "react";

import { primaryNavigation } from "../../config/navigation";

export function CommandPalette() {
  const [query, setQuery] = useState("");
  const results = useMemo(() => {
    const q = query.trim().toLowerCase();
    if (!q) return primaryNavigation;
    return primaryNavigation.filter((item) => item.label.toLowerCase().includes(q));
  }, [query]);

  return (
    <div className="rounded-lg border border-slate-700 bg-slate-900 p-3">
      <input
        value={query}
        onChange={(event) => setQuery(event.target.value)}
        placeholder="Jump to module..."
        className="w-full rounded border border-slate-700 bg-slate-950 px-2 py-1 text-sm"
      />
      <ul className="mt-2 space-y-1 text-sm">
        {results.map((item) => (
          <li key={item.href} className="rounded px-2 py-1 text-slate-300 hover:bg-slate-800">
            {item.label}
          </li>
        ))}
      </ul>
    </div>
  );
}
