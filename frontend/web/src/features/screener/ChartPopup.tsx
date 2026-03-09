"use client";

import { useEffect, useMemo, useRef } from "react";
import { createChart } from "lightweight-charts";
import { Button } from "@/components/ui/button";

type Candle = {
  timestamp: string;
  open: number;
  high: number;
  low: number;
  close: number;
};

type Props = {
  token: string;
  candles: Candle[];
  onClose: () => void;
};

export function ChartPopup({ token, candles, onClose }: Props) {
  const priceChartRef = useRef<HTMLDivElement | null>(null);
  const indicatorChartRef = useRef<HTMLDivElement | null>(null);
  const data = useMemo(
    () =>
      candles.map((c) => ({
        time: Math.floor(new Date(c.timestamp).getTime() / 1000) as never,
        open: c.open,
        high: c.high,
        low: c.low,
        close: c.close
      })),
    [candles]
  );

  const ema20 = useMemo(() => {
    const alpha = 2 / (20 + 1);
    const out: Array<{ time: never; value: number }> = [];
    let prev: number | null = null;
    for (const c of candles) {
      const price = c.close;
      prev = prev === null ? price : alpha * price + (1 - alpha) * prev;
      out.push({ time: Math.floor(new Date(c.timestamp).getTime() / 1000) as never, value: prev });
    }
    return out;
  }, [candles]);

  const rsi14 = useMemo(() => {
    const closes = candles.map((c) => c.close);
    const out: Array<{ time: never; value: number }> = [];
    for (let i = 14; i < closes.length; i++) {
      let gains = 0;
      let losses = 0;
      for (let j = i - 13; j <= i; j++) {
        const diff = closes[j] - closes[j - 1];
        if (diff >= 0) gains += diff;
        else losses += Math.abs(diff);
      }
      const avgGain = gains / 14;
      const avgLoss = losses / 14;
      const rs = avgLoss === 0 ? 100 : avgGain / avgLoss;
      const value = 100 - 100 / (1 + rs);
      out.push({ time: Math.floor(new Date(candles[i].timestamp).getTime() / 1000) as never, value });
    }
    return out;
  }, [candles]);

  const macd = useMemo(() => {
    const closes = candles.map((c) => c.close);
    const ema = (period: number) => {
      const a = 2 / (period + 1);
      const out: number[] = [];
      let prev: number | null = null;
      for (const v of closes) {
        prev = prev === null ? v : a * v + (1 - a) * prev;
        out.push(prev);
      }
      return out;
    };
    const ema12 = ema(12);
    const ema26 = ema(26);
    const macdLine = ema12.map((v, i) => v - ema26[i]);
    const signal: number[] = [];
    const alpha = 2 / (9 + 1);
    let prev: number | null = null;
    for (const v of macdLine) {
      prev = prev === null ? v : alpha * v + (1 - alpha) * prev;
      signal.push(prev);
    }
    return {
      macdLine: macdLine.map((v, i) => ({ time: Math.floor(new Date(candles[i].timestamp).getTime() / 1000) as never, value: v })),
      signal: signal.map((v, i) => ({ time: Math.floor(new Date(candles[i].timestamp).getTime() / 1000) as never, value: v }))
    };
  }, [candles]);

  useEffect(() => {
    if (!priceChartRef.current || !indicatorChartRef.current) return;
    const chart = createChart(priceChartRef.current, {
      width: 900,
      height: 320,
      layout: { background: { color: "#0f172a" }, textColor: "#e2e8f0" },
      grid: { vertLines: { color: "#1e293b" }, horzLines: { color: "#1e293b" } }
    });
    const series = chart.addCandlestickSeries({
      upColor: "#10b981",
      downColor: "#ef4444",
      borderVisible: false,
      wickUpColor: "#10b981",
      wickDownColor: "#ef4444"
    });
    series.setData(data);
    const emaSeries = chart.addLineSeries({ color: "#f59e0b", lineWidth: 2, title: "EMA 20" });
    emaSeries.setData(ema20);
    chart.timeScale().fitContent();

    const indicatorChart = createChart(indicatorChartRef.current, {
      width: 900,
      height: 180,
      layout: { background: { color: "#0f172a" }, textColor: "#e2e8f0" },
      grid: { vertLines: { color: "#1e293b" }, horzLines: { color: "#1e293b" } }
    });
    const rsiSeries = indicatorChart.addLineSeries({ color: "#22d3ee", lineWidth: 2, title: "RSI 14" });
    rsiSeries.setData(rsi14);
    const macdSeries = indicatorChart.addLineSeries({ color: "#60a5fa", lineWidth: 2, title: "MACD" });
    macdSeries.setData(macd.macdLine);
    const signalSeries = indicatorChart.addLineSeries({ color: "#f43f5e", lineWidth: 2, title: "MACD Signal" });
    signalSeries.setData(macd.signal);
    indicatorChart.timeScale().fitContent();

    return () => {
      chart.remove();
      indicatorChart.remove();
    };
  }, [data, ema20, macd.macdLine, macd.signal, rsi14]);

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/80 p-4">
      <div className="rounded-lg border border-slate-700 bg-slate-900 p-4">
        <div className="mb-3 flex items-center justify-between">
          <h3 className="text-sm font-semibold text-slate-100">{token} - Strike Candles</h3>
          <Button onClick={onClose} variant="outline" size="sm">
            Close
          </Button>
        </div>
        <div className="space-y-3">
          <div ref={priceChartRef} />
          <div ref={indicatorChartRef} />
        </div>
      </div>
    </div>
  );
}
