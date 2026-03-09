import Link from "next/link";

export default function NotFound() {
  return (
    <section className="flex flex-col items-center justify-center gap-4 rounded border border-slate-800 bg-slate-900 p-8">
      <h2 className="text-2xl font-bold text-slate-100">404</h2>
      <p className="text-slate-400">This page could not be found.</p>
      <div className="flex gap-3">
        <Link
          href="/"
          className="rounded bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-500"
        >
          Home
        </Link>
        <Link
          href="/screener"
          className="rounded border border-slate-600 px-4 py-2 text-sm font-medium text-slate-300 hover:bg-slate-800"
        >
          Screener
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
