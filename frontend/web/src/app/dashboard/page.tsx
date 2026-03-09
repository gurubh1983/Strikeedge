"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import {
  Activity,
  BarChart3,
  ChevronRight,
  TrendingUp,
  TrendingDown,
  Zap,
  Target,
  AlertCircle,
} from "lucide-react";
import {
  fetchMarketOverview,
  type MarketOverviewHeatmapItem,
  type MarketOverviewPayload,
  type MomentumMetrics,
} from "../../lib/api/client";

function getHeatmapBg(pct: number): string {
  if (pct === 0) return "bg-slate-700/80";
  const abs = Math.min(Math.abs(pct) / 3, 1);
  if (pct > 0) return abs >= 0.6 ? "bg-emerald-600" : abs >= 0.3 ? "bg-emerald-700/90" : "bg-emerald-800/70";
  return abs >= 0.6 ? "bg-rose-600" : abs >= 0.3 ? "bg-rose-700/90" : "bg-rose-800/70";
}

function StatCard({
  title,
  value,
  sub,
  positive,
  icon: Icon,
}: {
  title: string;
  value: string;
  sub?: string;
  positive?: boolean;
  icon: React.ElementType;
}) {
  return (
    <div className="rounded-xl border border-slate-700/60 bg-slate-900/80 p-4 shadow-lg backdrop-blur-sm transition-all hover:border-slate-600/80">
      <div className="flex items-start justify-between">
        <div>
          <p className="text-xs font-medium uppercase tracking-wider text-slate-400">{title}</p>
          <p className={`mt-1 text-xl font-bold tabular-nums ${positive === true ? "text-emerald-400" : positive === false ? "text-rose-400" : "text-white"}`}>
            {value}
          </p>
          {sub && <p className="mt-0.5 text-xs text-slate-500">{sub}</p>}
        </div>
        <div className="rounded-lg bg-slate-800/80 p-2">
          <Icon className="h-5 w-5 text-slate-400" />
        </div>
      </div>
    </div>
  );
}

function HeatmapTile({ item, href }: { item: MarketOverviewHeatmapItem; href: string }) {
  const pct = item.change_pct;
  return (
    <Link
      href={href}
      className={`group flex flex-col rounded-lg px-2.5 py-2 transition-all hover:scale-[1.02] hover:shadow-lg ${getHeatmapBg(pct)}`}
      title={item.ltp != null ? `${item.name}: ₹${item.ltp.toLocaleString()}` : item.name}
    >
      <span className="truncate text-xs font-semibold text-white/90 group-hover:text-white">
        {item.name}
      </span>
      <span className={`mt-0.5 text-sm font-bold tabular-nums ${pct >= 0 ? "text-emerald-100" : "text-rose-100"}`}>
        {pct >= 0 ? "+" : ""}
        {pct.toFixed(2)}%
      </span>
    </Link>
  );
}

function MarketContextBadge({ metrics }: { metrics: MomentumMetrics }) {
  const ctx = metrics.market_context;
  const styles: Record<string, { bg: string; text: string; icon: React.ElementType }> = {
    expansion: { bg: "bg-emerald-900/50 border-emerald-600/40", text: "text-emerald-300", icon: Zap },
    rotation: { bg: "bg-amber-900/40 border-amber-600/40", text: "text-amber-300", icon: BarChart3 },
    caution: { bg: "bg-amber-900/50 border-amber-700/50", text: "text-amber-200", icon: AlertCircle },
    contraction: { bg: "bg-rose-900/40 border-rose-600/40", text: "text-rose-300", icon: TrendingDown },
  };
  const s = styles[ctx] || styles.rotation;
  const Icon = s.icon;
  return (
    <div className={`flex items-center gap-3 rounded-xl border px-4 py-3 ${s.bg}`}>
      <Icon className={`h-6 w-6 ${s.text}`} />
      <div>
        <p className={`font-semibold ${s.text}`}>{metrics.context_label}</p>
        <p className="text-xs text-slate-400">{metrics.context_hint}</p>
      </div>
    </div>
  );
}

export default function DashboardPage() {
  const [data, setData] = useState<MarketOverviewPayload | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let mounted = true;
    setLoading(true);
    setError(null);
    fetchMarketOverview()
      .then((res) => {
        if (mounted) setData(res);
      })
      .catch((e) => {
        if (mounted) setError(e instanceof Error ? e.message : "Failed to load");
      })
      .finally(() => {
        if (mounted) setLoading(false);
      });
    return () => {
      mounted = false;
    };
  }, []);

  if (loading) {
    return (
      <div className="flex min-h-[60vh] items-center justify-center">
        <div className="flex flex-col items-center gap-4">
          <div className="h-10 w-10 animate-spin rounded-full border-2 border-cyan-500/30 border-t-cyan-400" />
          <p className="text-sm text-slate-400">Loading momentum dashboard...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="rounded-xl border border-rose-500/30 bg-slate-900/80 p-8">
        <p className="font-medium text-rose-200">{error}</p>
        <button
          type="button"
          onClick={() => window.location.reload()}
          className="mt-4 rounded-lg bg-slate-700 px-4 py-2 text-sm font-medium text-slate-200 hover:bg-slate-600"
        >
          Retry
        </button>
      </div>
    );
  }

  if (!data) return null;

  const metrics = data.momentum_metrics;
  const hasMetrics = metrics && Object.keys(metrics).length > 0;

  return (
    <div className="space-y-6 pb-8">
      {/* Header */}
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-white">
            Momentum Dashboard
          </h1>
          <p className="mt-1 text-sm text-slate-400">
            Sector rotation, breadth & heatmaps for momentum decisions
          </p>
        </div>
        <div className="flex items-center gap-3">
          {data.data_source === "previous_close" && (
            <span className="rounded-lg border border-amber-600/40 bg-amber-900/30 px-3 py-1.5 text-xs font-medium text-amber-200">
              EOD data
            </span>
          )}
          {data.data_source === "fallback" && (
            <span className="rounded-lg border border-slate-600 bg-slate-800 px-3 py-1.5 text-xs text-slate-400">
              Placeholder
            </span>
          )}
          <Link
            href="/scanner"
            className="flex items-center gap-2 rounded-lg bg-cyan-600/80 px-4 py-2 text-sm font-semibold text-white transition-colors hover:bg-cyan-500/90"
          >
            <Target className="h-4 w-4" />
            Scan Momentum
          </Link>
        </div>
      </div>

      {/* KPI Cards - TailAdmin style */}
      {hasMetrics && (
        <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
          <StatCard
            title="Nifty 50"
            value={`${(metrics!.nifty50_change >= 0 ? "+" : "")}${metrics!.nifty50_change.toFixed(2)}%`}
            positive={metrics!.nifty50_change >= 0}
            icon={Activity}
          />
          <StatCard
            title="Bank Nifty"
            value={`${(metrics!.bank_nifty_change >= 0 ? "+" : "")}${metrics!.bank_nifty_change.toFixed(2)}%`}
            positive={metrics!.bank_nifty_change >= 0}
            icon={BarChart3}
          />
          <StatCard
            title="Market Breadth"
            value={`${metrics!.breadth_pct}%`}
            sub={`${metrics!.advance_count} up / ${metrics!.decline_count} down`}
            icon={TrendingUp}
          />
          <StatCard
            title="Strongest Sector"
            value={metrics!.strongest_sector?.name ?? "—"}
            sub={
              metrics!.strongest_sector
                ? `${(metrics!.strongest_sector.change_pct >= 0 ? "+" : "")}${metrics!.strongest_sector.change_pct.toFixed(2)}%`
                : undefined
            }
            positive={true}
            icon={Zap}
          />
        </div>
      )}

      {/* Market Context - Decision input */}
      {hasMetrics && (
        <MarketContextBadge metrics={metrics!} />
      )}

      {/* Quick Actions */}
      <div className="flex flex-wrap gap-3">
        <Link
          href="/scanner"
          className="inline-flex items-center gap-2 rounded-lg border border-slate-600 bg-slate-800/60 px-4 py-2 text-sm font-medium text-slate-200 transition-colors hover:border-cyan-500/50 hover:bg-slate-800 hover:text-cyan-300"
        >
          RSI & EMA Scan
          <ChevronRight className="h-4 w-4" />
        </Link>
        <Link
          href="/screener"
          className="inline-flex items-center gap-2 rounded-lg border border-slate-600 bg-slate-800/60 px-4 py-2 text-sm font-medium text-slate-200 transition-colors hover:border-cyan-500/50 hover:bg-slate-800 hover:text-cyan-300"
        >
          Advanced Screener
          <ChevronRight className="h-4 w-4" />
        </Link>
      </div>

      {/* Heatmaps - Dribbble/TailAdmin card layout */}
      <div className="grid gap-6 lg:grid-cols-2">
        {/* Sector Rotation - Key for momentum */}
        <div className="rounded-xl border border-slate-700/60 bg-slate-900/60 shadow-xl">
          <div className="flex items-center justify-between border-b border-slate-700/80 px-5 py-4">
            <h2 className="font-semibold text-white">Sector Rotation</h2>
            <Link href="/sectors" className="text-xs font-medium text-cyan-400 hover:text-cyan-300">
              View all →
            </Link>
          </div>
          <div className="grid grid-cols-3 gap-2 p-4 sm:grid-cols-4">
            {data.sector_heatmap.map((item) => (
              <HeatmapTile
                key={item.symbol}
                item={item}
                href={`/sectors?highlight=${item.symbol}`}
              />
            ))}
          </div>
        </div>

        {/* Stock Heatmap */}
        <div className="rounded-xl border border-slate-700/60 bg-slate-900/60 shadow-xl">
          <div className="flex items-center justify-between border-b border-slate-700/80 px-5 py-4">
            <h2 className="font-semibold text-white">Nifty Stock Momentum</h2>
            <Link href="/stocks" className="text-xs font-medium text-cyan-400 hover:text-cyan-300">
              View all →
            </Link>
          </div>
          <div className="grid grid-cols-4 gap-2 p-4 sm:grid-cols-5">
            {data.stocks_heatmap.map((item) => (
              <HeatmapTile key={item.symbol} item={item} href={`/stocks?symbol=${item.symbol}`} />
            ))}
          </div>
        </div>
      </div>

      {/* Top Gainers / Losers - Decision cards */}
      <div className="grid gap-6 lg:grid-cols-2">
        <div className="rounded-xl border border-emerald-700/40 bg-slate-900/60 shadow-xl">
          <div className="flex items-center gap-2 border-b border-slate-700/80 px-5 py-3">
            <TrendingUp className="h-5 w-5 text-emerald-400" />
            <h2 className="font-semibold text-emerald-400">Top 5 Gainers</h2>
          </div>
          <div className="divide-y divide-slate-800/80">
            {data.top_winners.map((item, i) => (
              <Link
                key={`${item.symbol}-${i}`}
                href={item.symbol.startsWith("NIFTY") ? `/sectors?highlight=${item.symbol}` : `/stocks?symbol=${item.symbol}`}
                className="flex items-center justify-between px-5 py-3 transition-colors hover:bg-emerald-900/20"
              >
                <span className="font-medium text-slate-200">{item.name}</span>
                <span className="font-bold tabular-nums text-emerald-400">
                  +{item.change_pct.toFixed(2)}%
                </span>
              </Link>
            ))}
          </div>
        </div>

        <div className="rounded-xl border border-rose-700/40 bg-slate-900/60 shadow-xl">
          <div className="flex items-center gap-2 border-b border-slate-700/80 px-5 py-3">
            <TrendingDown className="h-5 w-5 text-rose-400" />
            <h2 className="font-semibold text-rose-400">Top 5 Losers</h2>
          </div>
          <div className="divide-y divide-slate-800/80">
            {data.top_losers.map((item, i) => (
              <Link
                key={`${item.symbol}-${i}`}
                href={item.symbol.startsWith("NIFTY") ? `/sectors?highlight=${item.symbol}` : `/stocks?symbol=${item.symbol}`}
                className="flex items-center justify-between px-5 py-3 transition-colors hover:bg-rose-900/20"
              >
                <span className="font-medium text-slate-200">{item.name}</span>
                <span className="font-bold tabular-nums text-rose-400">
                  {item.change_pct.toFixed(2)}%
                </span>
              </Link>
            ))}
          </div>
        </div>
      </div>

      {/* Momentum Insights - Decision summary */}
      {hasMetrics && (
        <div className="rounded-xl border border-slate-700/60 bg-gradient-to-br from-slate-900/80 to-slate-900/40 p-5">
          <h3 className="mb-3 font-semibold text-slate-200">Momentum Insights</h3>
          <ul className="space-y-2 text-sm text-slate-400">
            <li>• Avg stock change: <span className={metrics!.avg_stock_change >= 0 ? "text-emerald-400" : "text-rose-400"}>{(metrics!.avg_stock_change >= 0 ? "+" : "")}{metrics!.avg_stock_change.toFixed(2)}%</span></li>
            <li>• Avg sector change: <span className={metrics!.avg_sector_change >= 0 ? "text-emerald-400" : "text-rose-400"}>{(metrics!.avg_sector_change >= 0 ? "+" : "")}{metrics!.avg_sector_change.toFixed(2)}%</span></li>
            {metrics!.weakest_sector && (
              <li>• Weakest sector: <span className="text-rose-400">{metrics!.weakest_sector.name}</span> ({metrics!.weakest_sector.change_pct.toFixed(2)}%)</li>
            )}
          </ul>
        </div>
      )}
    </div>
  );
}
