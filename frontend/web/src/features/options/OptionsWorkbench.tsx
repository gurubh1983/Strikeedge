"use client";

import { useEffect, useMemo, useState } from "react";

import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Select } from "@/components/ui/select";
import { Table, TableBody, TableHead } from "@/components/ui/table";
import {
  calculateOptionsGreeks,
  fetchExpiries,
  fetchOIHeatmap,
  fetchOptionsChain,
  fetchOptionsMetrics,
  fetchStrikeCandles,
  fetchStrikeGreeks,
  type OIHeatmapPointPayload,
  type OptionsChainMetricsPayload,
  type OptionsChainRowPayload,
  type StrikeGreeksPayload
} from "@/lib/api/client";
import { ChartPopup } from "../screener/ChartPopup";

type FilterState = {
  ivMin: number;
  deltaMin: number;
  gammaMin: number;
  oiMin: number;
  oiChangePctMin: number;
  volumeMin: number;
};

type RowView = {
  strike: number;
  callSymbol: string | null;
  callLtp: number | null;
  callIv: number | null;
  callOi: number | null;
  putSymbol: string | null;
  putLtp: number | null;
  putIv: number | null;
  putOi: number | null;
  pcr: number | null;
  oiChange: number | null;
  callGreeks: StrikeGreeksPayload | null;
  putGreeks: StrikeGreeksPayload | null;
};

const defaultFilter: FilterState = {
  ivMin: 0,
  deltaMin: -1,
  gammaMin: 0,
  oiMin: 0,
  oiChangePctMin: -999,
  volumeMin: 0
};

function valueTone(value: number | null | undefined, highPositive = false): string {
  if (value == null) return "text-slate-500";
  if (value > 0) return highPositive ? "text-emerald-300" : "text-slate-200";
  if (value < 0) return "text-rose-300";
  return "text-slate-300";
}

export function OptionsWorkbench() {
  const [underlying, setUnderlying] = useState("NIFTY");
  const [expiry, setExpiry] = useState("2026-04-24");
  const [expiries, setExpiries] = useState<Array<{ date: string; iso: string; expiry: number }>>([]);
  const [spot, setSpot] = useState(24000);
  const [timeframe, setTimeframe] = useState<"1m" | "5m" | "15m">("5m");
  const [chain, setChain] = useState<OptionsChainRowPayload[]>([]);
  const [metrics, setMetrics] = useState<OptionsChainMetricsPayload | null>(null);
  const [heatmap, setHeatmap] = useState<OIHeatmapPointPayload[]>([]);
  const [greeks, setGreeks] = useState<Record<string, StrikeGreeksPayload>>({});
  const [filters, setFilters] = useState<FilterState>(defaultFilter);
  const [selectedSymbol, setSelectedSymbol] = useState<string | null>(null);
  const [selectedCandles, setSelectedCandles] = useState<Array<{ timestamp: string; open: number; high: number; low: number; close: number }>>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function loadAll(refreshChain: boolean) {
    setLoading(true);
    setError(null);
    try {
      const chainRows = await fetchOptionsChain({ underlying, expiry, limit: 120, refresh: refreshChain });
      setChain(chainRows);
      const m = await fetchOptionsMetrics(underlying, expiry);
      setMetrics(m);
      await calculateOptionsGreeks({
        underlying,
        expiry,
        spot,
        time_to_expiry_years: 20 / 365
      });

      const symbols = chainRows.flatMap((row) => [row.call_symbol, row.put_symbol]).filter(Boolean) as string[];
      const uniqueSymbols = Array.from(new Set(symbols)).slice(0, 96);
      const responses = await Promise.allSettled(uniqueSymbols.map((symbol) => fetchStrikeGreeks(symbol)));
      const nextGreeks: Record<string, StrikeGreeksPayload> = {};
      for (const response of responses) {
        if (response.status === "fulfilled") nextGreeks[response.value.symbol] = response.value;
      }
      setGreeks(nextGreeks);
      setHeatmap(await fetchOIHeatmap(underlying, expiry, 200));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load options data");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    fetchExpiries(underlying).then((r) => setExpiries(r.expiries || [])).catch(() => setExpiries([]));
  }, [underlying]);

  useEffect(() => {
    void loadAll(false);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  async function onOpenChart(symbol: string) {
    setSelectedSymbol(symbol);
    const candles = await fetchStrikeCandles(symbol, timeframe, 200);
    setSelectedCandles(candles);
  }

  const filteredRows = useMemo<RowView[]>(() => {
    const rows: RowView[] = chain.map((row) => {
      const callGreeks = row.call_symbol ? greeks[row.call_symbol] ?? null : null;
      const putGreeks = row.put_symbol ? greeks[row.put_symbol] ?? null : null;
      return {
        strike: row.strike_price,
        callSymbol: row.call_symbol,
        callLtp: row.call_ltp ?? null,
        callIv: row.call_iv,
        callOi: row.call_oi,
        putSymbol: row.put_symbol,
        putLtp: row.put_ltp ?? null,
        putIv: row.put_iv,
        putOi: row.put_oi,
        pcr: row.put_call_ratio,
        oiChange: row.total_oi_change,
        callGreeks,
        putGreeks
      };
    });

    return rows.filter((row) => {
      const callDelta = row.callGreeks?.delta ?? 0;
      const callGamma = row.callGreeks?.gamma ?? 0;
      const callIv = row.callIv ?? 0;
      const callOi = row.callOi ?? 0;
      const callVolume = Math.round(callOi / 8);
      const oiChangePct = row.callOi && row.oiChange ? (row.oiChange / row.callOi) * 100 : 0;
      return (
        callIv >= filters.ivMin &&
        callDelta >= filters.deltaMin &&
        callGamma >= filters.gammaMin &&
        callOi >= filters.oiMin &&
        oiChangePct >= filters.oiChangePctMin &&
        callVolume >= filters.volumeMin
      );
    });
  }, [chain, filters, greeks]);

  const oiMax = Math.max(1, ...heatmap.map((point) => point.total_oi));

  return (
    <section className="space-y-4">
      <Card>
        <h2 className="mb-3 text-lg font-semibold text-slate-100">Options Chain Workbench</h2>
        <div className="grid grid-cols-1 gap-2 md:grid-cols-6">
          <Select value={underlying} onChange={(e) => setUnderlying(e.target.value)}>
            <option value="NIFTY">NIFTY</option>
            <option value="BANKNIFTY">BANKNIFTY</option>
          </Select>
          <Select value={expiry} onChange={(e) => setExpiry(e.target.value)}>
            {expiries.map((e) => (
              <option key={e.expiry} value={e.iso || e.date}>
                {e.date}
              </option>
            ))}
            {expiries.length === 0 ? <option value={expiry}>{expiry}</option> : null}
          </Select>
          <Input type="number" value={spot} onChange={(e) => setSpot(Number(e.target.value))} placeholder="Spot" />
          <Select value={timeframe} onChange={(e) => setTimeframe(e.target.value as "1m" | "5m" | "15m")}>
            <option value="1m">1m chart</option>
            <option value="5m">5m chart</option>
            <option value="15m">15m chart</option>
          </Select>
          <Button onClick={() => void loadAll(true)} disabled={loading}>
            {loading ? "Loading..." : "Refresh Chain"}
          </Button>
          <Button variant="outline" onClick={() => setFilters(defaultFilter)}>
            Reset Filters
          </Button>
        </div>
        {error ? <p className="mt-2 text-sm text-rose-400">{error}</p> : null}
      </Card>

      <Card>
        <h3 className="mb-3 text-sm font-semibold text-slate-100">Option Filters</h3>
        <div className="grid grid-cols-2 gap-2 md:grid-cols-6">
          <Input type="number" value={filters.ivMin} onChange={(e) => setFilters((s) => ({ ...s, ivMin: Number(e.target.value) }))} placeholder="IV >=" />
          <Input type="number" value={filters.deltaMin} onChange={(e) => setFilters((s) => ({ ...s, deltaMin: Number(e.target.value) }))} placeholder="Delta >=" />
          <Input type="number" value={filters.gammaMin} onChange={(e) => setFilters((s) => ({ ...s, gammaMin: Number(e.target.value) }))} placeholder="Gamma >=" />
          <Input type="number" value={filters.oiMin} onChange={(e) => setFilters((s) => ({ ...s, oiMin: Number(e.target.value) }))} placeholder="OI >=" />
          <Input
            type="number"
            value={filters.oiChangePctMin}
            onChange={(e) => setFilters((s) => ({ ...s, oiChangePctMin: Number(e.target.value) }))}
            placeholder="OI chg% >="
          />
          <Input type="number" value={filters.volumeMin} onChange={(e) => setFilters((s) => ({ ...s, volumeMin: Number(e.target.value) }))} placeholder="Volume >=" />
        </div>
      </Card>

      {metrics ? (
        <Card>
          <h3 className="mb-2 text-sm font-semibold text-slate-100">Chain Summary</h3>
          <div className="grid grid-cols-2 gap-2 text-xs md:grid-cols-5">
            <p className="text-slate-300">Strikes: <span className="text-slate-100">{metrics.strikes}</span></p>
            <p className="text-slate-300">Call OI: <span className="text-slate-100">{metrics.total_call_oi}</span></p>
            <p className="text-slate-300">Put OI: <span className="text-slate-100">{metrics.total_put_oi}</span></p>
            <p className="text-slate-300">PCR: <span className="text-slate-100">{metrics.put_call_ratio ?? "-"}</span></p>
            <p className={valueTone(metrics.total_oi_change, true)}>Total OI change: {metrics.total_oi_change}</p>
          </div>
        </Card>
      ) : null}

      <Card>
        <h3 className="mb-2 text-sm font-semibold text-slate-100">Options Chain</h3>
        <div className="space-y-2 md:hidden">
          {filteredRows.map((row) => (
            <div key={row.strike} className="rounded border border-slate-800 p-2 text-xs">
              <p className="mb-1 text-sm font-semibold text-slate-100">Strike {row.strike}</p>
              <p className="text-slate-300">Call: {row.callSymbol ?? "-"}</p>
              <p className="text-emerald-300">Call LTP: {row.callLtp != null ? row.callLtp.toFixed(2) : "-"}</p>
              <p className={`${valueTone(row.callGreeks?.delta, true)}`}>Call Delta: {row.callGreeks?.delta ?? "-"}</p>
              <p className={`${valueTone(row.callGreeks?.gamma, true)}`}>Call Gamma: {row.callGreeks?.gamma ?? "-"}</p>
              <p className="text-slate-300">Put: {row.putSymbol ?? "-"}</p>
              <p className="text-rose-300">Put LTP: {row.putLtp != null ? row.putLtp.toFixed(2) : "-"}</p>
              <p className={`${valueTone(row.putGreeks?.delta, false)}`}>Put Delta: {row.putGreeks?.delta ?? "-"}</p>
              <div className="mt-2 flex gap-2">
                {row.callSymbol ? (
                  <Button size="sm" variant="outline" onClick={() => void onOpenChart(row.callSymbol!)}>
                    Call Chart
                  </Button>
                ) : null}
                {row.putSymbol ? (
                  <Button size="sm" variant="outline" onClick={() => void onOpenChart(row.putSymbol!)}>
                    Put Chart
                  </Button>
                ) : null}
              </div>
            </div>
          ))}
        </div>
        <div className="hidden overflow-x-auto md:block">
          <Table className="min-w-[1100px]">
            <TableHead>
              <tr>
                <th className="py-2">Call</th>
                <th className="py-2">LTP</th>
                <th className="py-2">IV</th>
                <th className="py-2">OI</th>
                <th className="py-2">Delta</th>
                <th className="py-2">Gamma</th>
                <th className="py-2">Strike</th>
                <th className="py-2">Put</th>
                <th className="py-2">LTP</th>
                <th className="py-2">IV</th>
                <th className="py-2">OI</th>
                <th className="py-2">Delta</th>
                <th className="py-2">Gamma</th>
                <th className="py-2">OI Δ</th>
                <th className="py-2">PCR</th>
              </tr>
            </TableHead>
            <TableBody>
              {filteredRows.map((row) => (
                <tr key={row.strike} className="border-t border-slate-800">
                  <td className="py-2 text-xs">
                    {row.callSymbol ? (
                      <button className="text-indigo-300 hover:underline" onClick={() => void onOpenChart(row.callSymbol!)}>
                        {row.callSymbol}
                      </button>
                    ) : (
                      "-"
                    )}
                  </td>
                  <td className="py-2 text-xs text-emerald-300 font-medium">{row.callLtp != null ? row.callLtp.toFixed(2) : "-"}</td>
                  <td className={`py-2 text-xs ${valueTone(row.callIv, true)}`}>{row.callIv ?? "-"}</td>
                  <td className={`py-2 text-xs ${valueTone(row.callOi, true)}`}>{row.callOi ?? "-"}</td>
                  <td className={`py-2 text-xs ${valueTone(row.callGreeks?.delta, true)}`}>{row.callGreeks?.delta ?? "-"}</td>
                  <td className={`py-2 text-xs ${valueTone(row.callGreeks?.gamma, true)}`}>{row.callGreeks?.gamma ?? "-"}</td>
                  <td className="py-2 text-sm font-semibold text-slate-100">{row.strike}</td>
                  <td className="py-2 text-xs">
                    {row.putSymbol ? (
                      <button className="text-indigo-300 hover:underline" onClick={() => void onOpenChart(row.putSymbol!)}>
                        {row.putSymbol}
                      </button>
                    ) : (
                      "-"
                    )}
                  </td>
                  <td className="py-2 text-xs text-rose-300 font-medium">{row.putLtp != null ? row.putLtp.toFixed(2) : "-"}</td>
                  <td className={`py-2 text-xs ${valueTone(row.putIv, true)}`}>{row.putIv ?? "-"}</td>
                  <td className={`py-2 text-xs ${valueTone(row.putOi, true)}`}>{row.putOi ?? "-"}</td>
                  <td className={`py-2 text-xs ${valueTone(row.putGreeks?.delta, false)}`}>{row.putGreeks?.delta ?? "-"}</td>
                  <td className={`py-2 text-xs ${valueTone(row.putGreeks?.gamma, true)}`}>{row.putGreeks?.gamma ?? "-"}</td>
                  <td className={`py-2 text-xs ${valueTone(row.oiChange, true)}`}>{row.oiChange ?? "-"}</td>
                  <td className="py-2 text-xs text-slate-300">{row.pcr ?? "-"}</td>
                </tr>
              ))}
            </TableBody>
          </Table>
        </div>
      </Card>

      <Card>
        <h3 className="mb-2 text-sm font-semibold text-slate-100">OI Heatmap Snapshot</h3>
        <div className="space-y-2">
          {heatmap.slice(0, 24).map((point, idx) => {
            const widthPct = Math.max(2, Math.round((point.total_oi / oiMax) * 100));
            return (
              <div key={`${point.strike_price}-${idx}`} className="rounded border border-slate-800 p-2">
                <div className="mb-1 flex justify-between text-xs">
                  <span className="text-slate-300">Strike {point.strike_price}</span>
                  <span className={valueTone(point.total_oi_change_pct, true)}>{point.total_oi_change_pct}%</span>
                </div>
                <div className="h-2 rounded bg-slate-800">
                  <div
                    className={`h-2 rounded ${point.total_oi_change >= 0 ? "bg-emerald-500" : "bg-rose-500"}`}
                    style={{ width: `${widthPct}%` }}
                  />
                </div>
              </div>
            );
          })}
        </div>
      </Card>

      {selectedSymbol ? <ChartPopup token={selectedSymbol} candles={selectedCandles} onClose={() => setSelectedSymbol(null)} /> : null}
    </section>
  );
}
