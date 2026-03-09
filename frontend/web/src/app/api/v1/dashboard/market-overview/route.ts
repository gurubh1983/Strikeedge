import { NextResponse } from "next/server";

const BACKEND_URL = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";

/** Proxy to backend dashboard API. Tries primary path, then /dashboard-overview fallback. */
export async function GET() {
  const primary = `${BACKEND_URL}/api/v1/dashboard/market-overview`;
  const fallbackPath = `${BACKEND_URL}/dashboard-overview`;

  try {
    let res = await fetch(primary, {
      headers: { "Content-Type": "application/json" },
      next: { revalidate: 60 },
    });
    if (res.status === 404) {
      res = await fetch(fallbackPath, {
        headers: { "Content-Type": "application/json" },
        next: { revalidate: 60 },
      });
    }
    if (!res.ok) {
      if (res.status === 404) {
        return NextResponse.json(fallbackResponse());
      }
      return NextResponse.json(
        { detail: `Backend error: ${res.status}` },
        { status: res.status }
      );
    }
    const data = await res.json();
    return NextResponse.json(data);
  } catch (e) {
    return NextResponse.json(fallbackResponse());
  }
}

function fallbackResponse() {
  const names = ["RELIANCE", "TCS", "HDFCBANK", "INFY", "ICICIBANK", "SBIN", "BHARTIARTL", "ITC", "KOTAKBANK", "LT", "AXISBANK", "MARUTI", "HCLTECH", "WIPRO", "SUNPHARMA", "TITAN", "ASIANPAINT", "ULTRACEMCO", "NESTLEIND", "BAJFINANCE"];
  const stocks = names.map((name) => ({ symbol: name, name, change_pct: 0, ltp: null }));
  const sectors = [
    { symbol: "NIFTY50", name: "Nifty 50", change_pct: 0, ltp: null },
    { symbol: "NIFTYBANK", name: "Bank Nifty", change_pct: 0, ltp: null },
    { symbol: "NIFTYAUTO", name: "Auto", change_pct: 0, ltp: null },
    { symbol: "NIFTYIT", name: "IT", change_pct: 0, ltp: null },
    { symbol: "NIFTYPHARMA", name: "Pharma", change_pct: 0, ltp: null },
    { symbol: "NIFTYFMCG", name: "FMCG", change_pct: 0, ltp: null },
    { symbol: "NIFTYMETAL", name: "Metal", change_pct: 0, ltp: null },
    { symbol: "NIFTYENERGY", name: "Energy", change_pct: 0, ltp: null },
    { symbol: "NIFTYREALTY", name: "Realty", change_pct: 0, ltp: null },
  ];
  return {
    data_source: "fallback",
    stocks_heatmap: stocks,
    sector_heatmap: sectors,
    top_winners: stocks.slice(0, 5),
    top_losers: stocks.slice(5, 10),
    momentum_metrics: {
      advance_count: 0,
      decline_count: 0,
      breadth_pct: 50,
      avg_stock_change: 0,
      avg_sector_change: 0,
      strongest_sector: null,
      weakest_sector: null,
      market_context: "rotation",
      context_label: "Rotation",
      context_hint: "Restart backend for live data",
      nifty50_change: 0,
      bank_nifty_change: 0,
    },
  };
}
