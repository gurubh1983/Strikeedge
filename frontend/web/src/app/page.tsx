import Link from "next/link";

export default function HomePage() {
  return (
    <section className="rounded border border-slate-800 bg-slate-900 p-6">
      <h2 className="text-lg font-semibold text-slate-100">Welcome to StrikeEdge</h2>
      <p className="mt-2 text-sm text-slate-300">
        Use the Screener or Scanner for live rule-based scans and strike chart drill-down.
      </p>
      <div className="mt-4 flex gap-3">
        <Link
          href="/screener"
          className="rounded bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-500"
        >
          Open Screener
        </Link>
        <Link
          href="/scanner"
          className="rounded border border-slate-600 px-4 py-2 text-sm font-medium text-slate-300 hover:bg-slate-800"
        >
          Open Scanner
        </Link>
        <Link
          href="/dashboard"
          className="rounded border border-slate-600 px-4 py-2 text-sm font-medium text-slate-300 hover:bg-slate-800"
        >
          Dashboard
        </Link>
      </div>
    </section>
  );
}
