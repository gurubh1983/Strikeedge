"use client";

import React, { useEffect, useMemo, useRef, useState } from "react";
import {
  Bell,
  Calculator,
  ChevronDown,
  Copy,
  Files,
  GripVertical,
  History,
  MoreHorizontal,
  Play,
  Search,
  Sparkles,
  X,
} from "lucide-react";

import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Select } from "@/components/ui/select";
import { Table, TableBody, TableHead } from "@/components/ui/table";
import { useAuthActor } from "@/hooks/use-auth-actor";
import {
  createScreener,
  fetchChart,
  fetchFyersStatus,
  fetchInstruments,
  fetchScanResults,
  fetchStrikeCandles,
  getScreener,
  listScreeners,
  runScan,
  runTechnicalScan,
  type ScanGroup,
  type ScanResult,
  type ScreenerPayload,
  type TechnicalScanResult,
} from "../../lib/api/client";
import { ChartPopup } from "./ChartPopup";

type SortKey = "token" | "matched";

// --- Advanced Filter types & helpers (from additionalfeatures) ---
interface IndicatorValue {
  type: "indicator" | "number" | "expression";
  indicator?: string;
  params?: Record<string, number>;
  value?: number;
  offset?: number;
  expression?: { type: "operator"; operator?: string; left?: IndicatorValue; right?: IndicatorValue };
}

interface FilterCondition {
  id: string;
  left: IndicatorValue;
  operator: string;
  right: IndicatorValue;
  right2?: IndicatorValue;
  timeframe: string;
}

interface FilterGroup {
  id: string;
  logic: "AND" | "OR";
  conditions: FilterCondition[];
}

const INDICATOR_TO_API: Record<string, string> = {
  RSI: "rsi_14",
  EMA: "ema_20",
  MACD: "macd",
  MACD_SIGNAL: "macd_signal",
};

const OPERATOR_TO_API: Record<string, string> = {
  gt: ">",
  gte: ">=",
  lt: "<",
  lte: "<=",
  eq: "==",
};

function conditionsToRules(groups: FilterGroup[]): { indicator: string; operator: ">" | "<" | ">=" | "<=" | "=="; value: number }[] {
  const rules: { indicator: string; operator: ">" | "<" | ">=" | "<=" | "=="; value: number }[] = [];
  for (const g of groups) {
    for (const c of g.conditions) {
      if (c.left.type !== "indicator" || c.right.type !== "number") continue;
      const apiInd = INDICATOR_TO_API[c.left.indicator ?? ""];
      if (!apiInd) continue;
      const apiOp = OPERATOR_TO_API[c.operator];
      if (!apiOp) continue;
      rules.push({ indicator: apiInd, operator: apiOp as ">" | "<" | ">=" | "<=" | "==", value: c.right.value ?? 0 });
    }
  }
  return rules;
}

/** Convert advanced groups to filter_config for backend FilterEngine (70+ indicators). */
function groupsToFilterConfig(groups: FilterGroup[]): { groups: Array<{ logic: "AND" | "OR"; conditions: unknown[] }>; group_logic: "AND" | "OR" } {
  return {
    groups: groups
      .filter((g) => g.conditions.length > 0)
      .map((g) => ({
        logic: g.logic,
        conditions: g.conditions.map((c) => ({
          left: c.left,
          operator: c.operator,
          right: c.right,
        })),
      })),
    group_logic: "AND",
  };
}

type IndParam = { name: string; default: number; min?: number; max?: number };
const SUPPORTED_INDICATORS: { code: string; name: string; category: string; params: IndParam[] }[] = [
  { code: "OPEN", name: "Open", category: "Price", params: [] },
  { code: "HIGH", name: "High", category: "Price", params: [] },
  { code: "LOW", name: "Low", category: "Price", params: [] },
  { code: "CLOSE", name: "Close", category: "Price", params: [] },
  { code: "VWAP", name: "VWAP", category: "Price", params: [] },
  { code: "TYPICAL", name: "Typical Price", category: "Price", params: [] },
  { code: "SMA", name: "SMA", category: "Moving Averages", params: [{ name: "period", default: 20, min: 1, max: 500 }] },
  { code: "EMA", name: "EMA", category: "Moving Averages", params: [{ name: "period", default: 20, min: 1, max: 500 }] },
  { code: "WMA", name: "WMA", category: "Moving Averages", params: [{ name: "period", default: 20, min: 1, max: 500 }] },
  { code: "DEMA", name: "DEMA", category: "Moving Averages", params: [{ name: "period", default: 20, min: 1, max: 500 }] },
  { code: "TEMA", name: "TEMA", category: "Moving Averages", params: [{ name: "period", default: 20, min: 1, max: 500 }] },
  { code: "HMA", name: "Hull MA", category: "Moving Averages", params: [{ name: "period", default: 20, min: 1, max: 500 }] },
  { code: "KAMA", name: "KAMA", category: "Moving Averages", params: [{ name: "period", default: 20, min: 1, max: 500 }] },
  { code: "RSI", name: "RSI", category: "Momentum", params: [{ name: "period", default: 14, min: 2, max: 100 }] },
  { code: "RSI_SMA", name: "RSI SMA", category: "Momentum", params: [{ name: "rsi", default: 14 }, { name: "sma", default: 14 }] },
  { code: "STOCH_K", name: "Stoch %K", category: "Momentum", params: [{ name: "k", default: 14 }, { name: "smooth", default: 3 }] },
  { code: "STOCH_D", name: "Stoch %D", category: "Momentum", params: [{ name: "k", default: 14 }, { name: "d", default: 3 }] },
  { code: "CCI", name: "CCI", category: "Momentum", params: [{ name: "period", default: 20 }] },
  { code: "WILLR", name: "Williams %R", category: "Momentum", params: [{ name: "period", default: 14 }] },
  { code: "MFI", name: "MFI", category: "Momentum", params: [{ name: "period", default: 14 }] },
  { code: "ROC", name: "ROC", category: "Momentum", params: [{ name: "period", default: 10 }] },
  { code: "MOMENTUM", name: "Momentum", category: "Momentum", params: [{ name: "period", default: 10 }] },
  { code: "MACD", name: "MACD Line", category: "Trend", params: [{ name: "fast", default: 12 }, { name: "slow", default: 26 }] },
  { code: "MACD_SIGNAL", name: "MACD Signal", category: "Trend", params: [{ name: "fast", default: 12 }, { name: "slow", default: 26 }, { name: "signal", default: 9 }] },
  { code: "MACD_HIST", name: "MACD Histogram", category: "Trend", params: [{ name: "fast", default: 12 }, { name: "slow", default: 26 }, { name: "signal", default: 9 }] },
  { code: "ADX", name: "ADX", category: "Trend", params: [{ name: "period", default: 14 }] },
  { code: "PLUS_DI", name: "+DI", category: "Trend", params: [{ name: "period", default: 14 }] },
  { code: "MINUS_DI", name: "-DI", category: "Trend", params: [{ name: "period", default: 14 }] },
  { code: "SUPERTREND", name: "Supertrend", category: "Trend", params: [{ name: "period", default: 10 }, { name: "mult", default: 3 }] },
  { code: "PSAR", name: "Parabolic SAR", category: "Trend", params: [{ name: "af", default: 0.02 }, { name: "max", default: 0.2 }] },
  { code: "AROON_UP", name: "Aroon Up", category: "Trend", params: [{ name: "period", default: 25 }] },
  { code: "AROON_DOWN", name: "Aroon Down", category: "Trend", params: [{ name: "period", default: 25 }] },
  { code: "ATR", name: "ATR", category: "Volatility", params: [{ name: "period", default: 14 }] },
  { code: "BB_UPPER", name: "BB Upper", category: "Volatility", params: [{ name: "period", default: 20 }, { name: "std", default: 2 }] },
  { code: "BB_MIDDLE", name: "BB Middle", category: "Volatility", params: [{ name: "period", default: 20 }] },
  { code: "BB_LOWER", name: "BB Lower", category: "Volatility", params: [{ name: "period", default: 20 }, { name: "std", default: 2 }] },
  { code: "BB_WIDTH", name: "BB Width", category: "Volatility", params: [{ name: "period", default: 20 }] },
  { code: "BB_PERCENT", name: "BB %B", category: "Volatility", params: [{ name: "period", default: 20 }] },
  { code: "KC_UPPER", name: "Keltner Upper", category: "Volatility", params: [{ name: "period", default: 20 }] },
  { code: "KC_LOWER", name: "Keltner Lower", category: "Volatility", params: [{ name: "period", default: 20 }] },
  { code: "DC_UPPER", name: "Donchian Upper", category: "Volatility", params: [{ name: "period", default: 20 }] },
  { code: "DC_LOWER", name: "Donchian Lower", category: "Volatility", params: [{ name: "period", default: 20 }] },
  { code: "VOLUME", name: "Volume", category: "Volume", params: [] },
  { code: "VOLUME_SMA", name: "Volume SMA", category: "Volume", params: [{ name: "period", default: 20 }] },
  { code: "OBV", name: "OBV", category: "Volume", params: [] },
  { code: "CMF", name: "CMF", category: "Volume", params: [{ name: "period", default: 20 }] },
  { code: "ADL", name: "A/D Line", category: "Volume", params: [] },
  { code: "VWMA", name: "VWMA", category: "Volume", params: [{ name: "period", default: 20 }] },
  { code: "DOJI", name: "Doji", category: "Patterns", params: [] },
  { code: "HAMMER", name: "Hammer", category: "Patterns", params: [] },
  { code: "ENGULF_BULL", name: "Bullish Engulfing", category: "Patterns", params: [] },
  { code: "ENGULF_BEAR", name: "Bearish Engulfing", category: "Patterns", params: [] },
  { code: "PDH", name: "Prev Day High", category: "Price Action", params: [] },
  { code: "PDL", name: "Prev Day Low", category: "Price Action", params: [] },
  { code: "PDC", name: "Prev Day Close", category: "Price Action", params: [] },
  { code: "PIVOT", name: "Pivot", category: "Pivots", params: [] },
  { code: "R1", name: "R1", category: "Pivots", params: [] },
  { code: "S1", name: "S1", category: "Pivots", params: [] },
  { code: "DELTA", name: "Delta", category: "Options", params: [] },
  { code: "GAMMA", name: "Gamma", category: "Options", params: [] },
  { code: "THETA", name: "Theta", category: "Options", params: [] },
  { code: "VEGA", name: "Vega", category: "Options", params: [] },
  { code: "IV", name: "IV", category: "Options", params: [] },
  { code: "IV_RANK", name: "IV Rank", category: "Options", params: [] },
  { code: "OI", name: "Open Interest", category: "Options", params: [] },
  { code: "OI_CHG", name: "OI Change", category: "Options", params: [] },
  { code: "OI_CHG_PCT", name: "OI Change %", category: "Options", params: [] },
  { code: "PCR", name: "Put Call Ratio", category: "Options", params: [] },
  { code: "VOL_OI", name: "Volume/OI", category: "Options", params: [] },
  { code: "MAX_PAIN", name: "Max Pain", category: "Options", params: [] },
];

const COMPARISON_OPS = [
  { value: "gt", label: ">", fullLabel: "Greater Than", category: "Comparison" },
  { value: "gte", label: "≥", fullLabel: "Greater or Equal", category: "Comparison" },
  { value: "lt", label: "<", fullLabel: "Less Than", category: "Comparison" },
  { value: "lte", label: "≤", fullLabel: "Less or Equal", category: "Comparison" },
  { value: "eq", label: "=", fullLabel: "Equals", category: "Comparison" },
  { value: "neq", label: "≠", fullLabel: "Not Equals", category: "Comparison" },
];

const CROSSOVER_OPS = [
  { value: "crosses_above", label: "⬆ Cross", fullLabel: "Crosses Above", category: "Crossover" },
  { value: "crosses_below", label: "⬇ Cross", fullLabel: "Crosses Below", category: "Crossover" },
  { value: "crosses", label: "✕ Cross", fullLabel: "Crosses (Either)", category: "Crossover" },
];

const RANGE_OPS = [
  { value: "between", label: "Between", fullLabel: "Is Between X and Y", category: "Range" },
  { value: "not_between", label: "Not Btwn", fullLabel: "Not Between", category: "Range" },
  { value: "within_pct", label: "Within %", fullLabel: "Within X% of", category: "Range" },
];

const CHANGE_OPS = [
  { value: "rising", label: "↗ Rising", fullLabel: "Rising for N bars", category: "Change" },
  { value: "falling", label: "↘ Falling", fullLabel: "Falling for N bars", category: "Change" },
  { value: "pct_change_gt", label: "%Δ >", fullLabel: "% Change Greater Than", category: "Change" },
  { value: "pct_change_lt", label: "%Δ <", fullLabel: "% Change Less Than", category: "Change" },
];

const POSITION_OPS = [
  { value: "highest_in", label: "Highest", fullLabel: "Is Highest in N bars", category: "Position" },
  { value: "lowest_in", label: "Lowest", fullLabel: "Is Lowest in N bars", category: "Position" },
  { value: "above_avg", label: "> Avg", fullLabel: "Above N-bar Average", category: "Position" },
  { value: "below_avg", label: "< Avg", fullLabel: "Below N-bar Average", category: "Position" },
];

const ALL_OPERATORS = [...COMPARISON_OPS, ...CROSSOVER_OPS, ...RANGE_OPS, ...CHANGE_OPS, ...POSITION_OPS];

const ADV_TIMEFRAMES = [
  { value: "1m", label: "1m" },
  { value: "3m", label: "3m" },
  { value: "5m", label: "5m" },
  { value: "15m", label: "15m" },
  { value: "30m", label: "30m" },
  { value: "1h", label: "1H" },
  { value: "4h", label: "4H" },
  { value: "1d", label: "D" },
  { value: "1w", label: "W" },
];

const OFFSET_OPTIONS = [
  { value: 0, label: "Current" },
  { value: 1, label: "[1] Prev" },
  { value: 2, label: "[2]" },
  { value: 3, label: "[3]" },
  { value: 5, label: "[5]" },
  { value: 10, label: "[10]" },
];

const DEFAULT_ADVANCED_GROUPS: FilterGroup[] = [
  {
    id: "1",
    logic: "AND",
    conditions: [
      {
        id: "1-1",
        left: { type: "indicator", indicator: "RSI", params: { period: 14 }, offset: 0 },
        operator: "gt",
        right: { type: "number", value: 60 },
        timeframe: "15m",
      },
    ],
  },
];

function IndicatorSelectorInline({
  value,
  onChange,
  showNumber = true,
}: {
  value: IndicatorValue;
  onChange: (v: IndicatorValue) => void;
  showNumber?: boolean;
}) {
  const [open, setOpen] = useState(false);
  const [showOffsetPicker, setShowOffsetPicker] = useState(false);
  const [search, setSearch] = useState("");
  const ref = useRef<HTMLDivElement>(null);
  useEffect(() => {
    const h = (e: MouseEvent) => {
      if (ref.current && !ref.current.contains(e.target as Node)) {
        setOpen(false);
        setShowOffsetPicker(false);
      }
    };
    document.addEventListener("mousedown", h);
    return () => document.removeEventListener("mousedown", h);
  }, []);

  const ind = value.type === "indicator" ? SUPPORTED_INDICATORS.find((i) => i.code === value.indicator) : null;
  const filtered = SUPPORTED_INDICATORS.filter(
    (i) => i.name.toLowerCase().includes(search.toLowerCase()) || i.code.toLowerCase().includes(search.toLowerCase())
  );
  const byCategory = filtered.reduce(
    (acc, i) => {
      const cat = i.category ?? "Other";
      if (!acc[cat]) acc[cat] = [];
      acc[cat].push(i);
      return acc;
    },
    {} as Record<string, (typeof SUPPORTED_INDICATORS)[number][]>
  );

  const handleParamChange = (paramName: string, newVal: number) => {
    if (value.type === "indicator")
      onChange({ ...value, params: { ...value.params, [paramName]: newVal } });
  };

  return (
    <div className="relative inline-flex items-center gap-0.5" ref={ref}>
      {value.type === "indicator" && ind ? (
        <div className="flex items-center rounded border border-slate-600 bg-slate-700/50 px-1.5 py-0.5">
          <span
            className="cursor-pointer px-0.5 text-xs font-medium text-slate-200 hover:text-blue-400"
            onClick={() => setOpen(true)}
          >
            {ind.name}
          </span>
          {ind.params.length > 0 && (
            <>
              <span className="text-xs text-slate-500">(</span>
              {ind.params.map((param, idx) => (
                <React.Fragment key={param.name}>
                  <input
                    type="number"
                    value={value.params?.[param.name] ?? param.default}
                    onChange={(e) =>
                      handleParamChange(
                        param.name,
                        parseInt(String(e.target.value), 10) || param.default
                      )
                    }
                    className="mx-0.5 w-8 rounded bg-blue-600 text-center text-xs font-bold text-white [appearance:textfield] focus:outline-none focus:ring-1 focus:ring-blue-400 [&::-webkit-inner-spin-button]:appearance-none [&::-webkit-outer-spin-button]:appearance-none"
                    min={param.min}
                    max={param.max}
                  />
                  {idx < ind.params.length - 1 && <span className="text-slate-500">,</span>}
                </React.Fragment>
              ))}
              <span className="text-slate-500">)</span>
            </>
          )}
          {(value.offset ?? 0) > 0 && (
            <span
              className="ml-0.5 cursor-pointer text-xs font-bold text-amber-400 hover:text-amber-300"
              onClick={() => setShowOffsetPicker(true)}
            >
              [{value.offset}]
            </span>
          )}
        </div>
      ) : value.type === "number" ? (
        <input
          type="number"
          value={value.value ?? 0}
          onChange={(e) => onChange({ type: "number", value: parseFloat(String(e.target.value)) || 0 })}
          className="w-16 rounded border border-slate-600 bg-blue-600 px-2 py-1 text-center text-xs font-bold text-white [appearance:textfield] focus:outline-none focus:ring-1 focus:ring-blue-400 [&::-webkit-inner-spin-button]:appearance-none [&::-webkit-outer-spin-button]:appearance-none"
        />
      ) : (
        <button
          onClick={() => setOpen(true)}
          className="rounded border border-slate-600 px-2 py-1 text-xs text-blue-400 hover:bg-slate-700"
        >
          Select...
        </button>
      )}
      <button onClick={() => setOpen(!open)} className="p-0.5 text-slate-500 hover:text-blue-400">
        <ChevronDown size={12} />
      </button>
      {value.type === "indicator" && (
        <button
          onClick={() => setShowOffsetPicker(!showOffsetPicker)}
          className={`rounded p-0.5 text-xs ${(value.offset ?? 0) > 0 ? "text-amber-400" : "text-slate-500 hover:text-amber-400"}`}
          title="Candle offset [1]=previous"
        >
          [n]
        </button>
      )}
      {showOffsetPicker && (
        <div className="absolute top-full left-0 z-50 mt-1 w-28 rounded-lg border border-slate-600 bg-slate-800 py-1 shadow-xl">
          <div className="px-2 py-1 text-[10px] uppercase text-slate-400">Offset</div>
          {OFFSET_OPTIONS.map((opt) => (
            <div
              key={opt.value}
              onClick={() => {
                onChange({ ...value, offset: opt.value });
                setShowOffsetPicker(false);
              }}
              className={`cursor-pointer px-3 py-1.5 text-xs hover:bg-slate-700 ${
                value.offset === opt.value ? "bg-blue-600/30 text-blue-400" : "text-slate-300"
              }`}
            >
              {opt.label}
            </div>
          ))}
        </div>
      )}
      {open && (
        <div className="absolute top-full left-0 z-50 mt-1 w-72 overflow-hidden rounded-lg border border-slate-600 bg-slate-800 shadow-xl">
          {showNumber && (
            <div
              onClick={() => {
                onChange({ type: "number", value: 0 });
                setOpen(false);
              }}
              className="flex cursor-pointer items-center gap-2 border-b border-slate-700 px-3 py-2 text-xs font-medium text-blue-400 hover:bg-slate-700"
            >
              <Calculator size={14} /> Enter Number Value
            </div>
          )}
          <div className="border-b border-slate-700 p-2">
            <div className="relative">
              <Search size={14} className="absolute left-2 top-1/2 -translate-y-1/2 text-slate-500" />
              <input
                type="text"
                placeholder="Search indicators..."
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                className="w-full rounded border border-slate-600 bg-slate-700 py-1.5 pl-7 pr-2 text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
              />
            </div>
          </div>
          <div className="max-h-72 overflow-y-auto">
            {Object.entries(byCategory).map(([cat, items]) => (
              <div key={cat}>
                <div className="sticky top-0 bg-slate-900/50 px-2 py-1.5 text-[10px] font-semibold uppercase tracking-wider text-slate-500">
                  {cat}
                </div>
                {items.map((i) => (
                  <div
                    key={i.code}
                    onClick={() => {
                      const params: Record<string, number> = {};
                      i.params.forEach((p) => (params[p.name] = p.default));
                      onChange({ type: "indicator", indicator: i.code, params, offset: value.offset ?? 0 });
                      setOpen(false);
                    }}
                    className={`cursor-pointer px-3 py-1.5 text-xs hover:bg-slate-700 ${
                      value.indicator === i.code ? "bg-blue-600/20 text-blue-400" : "text-slate-300"
                    }`}
                  >
                    {i.name}
                    {i.params.length > 0 && (
                      <span className="ml-1 text-slate-500">
                        ({i.params.map((p) => p.default).join(",")})
                      </span>
                    )}
                  </div>
                ))}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

function OperatorSelectorInline({ value, onChange }: { value: string; onChange: (v: string) => void }) {
  const [open, setOpen] = useState(false);
  const ref = useRef<HTMLDivElement>(null);
  useEffect(() => {
    const h = (e: MouseEvent) => {
      if (ref.current && !ref.current.contains(e.target as Node)) setOpen(false);
    };
    document.addEventListener("mousedown", h);
    return () => document.removeEventListener("mousedown", h);
  }, []);

  const sel = ALL_OPERATORS.find((o) => o.value === value);
  const operatorCategories = ["Comparison", "Crossover", "Range", "Change", "Position"];

  return (
    <div className="relative" ref={ref}>
      <button
        onClick={() => setOpen(!open)}
        className="min-w-[36px] rounded border border-amber-700/50 bg-amber-900/30 px-2 py-1 text-xs font-bold text-amber-400 hover:bg-amber-900/50"
      >
        {sel?.label ?? ">"}
      </button>
      {open && (
        <div className="absolute left-1/2 top-full z-50 mt-1 max-h-80 -translate-x-1/2 overflow-y-auto rounded-lg border border-slate-600 bg-slate-800 py-1 shadow-xl">
          {operatorCategories.map((category) => {
            const ops = ALL_OPERATORS.filter((o) => o.category === category);
            if (ops.length === 0) return null;
            return (
              <div key={category}>
                <div className="sticky top-0 bg-slate-900/50 px-2 py-1 text-[10px] font-semibold uppercase text-slate-500">
                  {category}
                </div>
                {ops.map((op) => (
                  <div
                    key={op.value}
                    onClick={() => {
                      onChange(op.value);
                      setOpen(false);
                    }}
                    className={`flex cursor-pointer items-center gap-2 px-3 py-1.5 text-xs hover:bg-slate-700 ${
                      value === op.value ? "bg-blue-600/20 text-blue-400" : "text-slate-300"
                    }`}
                  >
                    <span className="w-12 font-bold text-amber-400">{op.label}</span>
                    <span className="text-[11px] text-slate-400">{op.fullLabel}</span>
                  </div>
                ))}
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}

function AdvancedFilterPanelInline({
  groups,
  setGroups,
}: {
  groups: FilterGroup[];
  setGroups: React.Dispatch<React.SetStateAction<FilterGroup[]>>;
}) {
  const addCondition = (groupId: string) => {
    setGroups((prev) =>
      prev.map((g) =>
        g.id === groupId
          ? {
              ...g,
              conditions: [
                ...g.conditions,
                {
                  id: `${groupId}-${Date.now()}`,
                  left: { type: "indicator", indicator: "RSI", params: { period: 14 }, offset: 0 },
                  operator: "gt",
                  right: { type: "number", value: 60 },
                  timeframe: "15m",
                },
              ],
            }
          : g
      )
    );
  };

  const addGroup = () => {
    setGroups((prev) => [...prev, { id: Date.now().toString(), logic: "OR", conditions: [] }]);
  };

  const updateCondition = (id: string, u: Partial<FilterCondition>) => {
    setGroups((prev) =>
      prev.map((g) => ({
        ...g,
        conditions: g.conditions.map((c) => (c.id === id ? { ...c, ...u } : c)),
      }))
    );
  };

  const deleteCondition = (id: string) => {
    setGroups((prev) =>
      prev.map((g) => ({ ...g, conditions: g.conditions.filter((c) => c.id !== id) }))
    );
  };

  const duplicateCondition = (id: string) => {
    setGroups((prev) =>
      prev.map((g) => {
        const idx = g.conditions.findIndex((c) => c.id === id);
        if (idx === -1) return g;
        const newC = { ...g.conditions[idx], id: `${g.id}-${Date.now()}` };
        return {
          ...g,
          conditions: [...g.conditions.slice(0, idx + 1), newC, ...g.conditions.slice(idx + 1)],
        };
      })
    );
  };

  return (
    <div className="space-y-3">
      <div className="flex items-center gap-2 text-xs text-slate-400">
        <span>Strike passes</span>
        <strong className="text-slate-200">all</strong>
        <span>filters across</span>
        <strong className="text-blue-400">all F&O</strong>
        <span>(NIFTY, BANKNIFTY, FINNIFTY — all expiries)</span>
      </div>

      {groups.map((group, gi) => (
        <div key={group.id} className="space-y-2">
          {gi > 0 && (
            <div className="flex items-center gap-2">
              <div className="h-px flex-1 bg-slate-700" />
              <button
                onClick={() =>
                  setGroups((prev) =>
                    prev.map((g) =>
                      g.id === group.id ? { ...g, logic: g.logic === "AND" ? "OR" : "AND" } : g
                    )
                  )
                }
                className="rounded-full border border-amber-700/50 bg-amber-900/30 px-3 py-1 text-xs font-bold text-amber-400 hover:bg-amber-900/50"
              >
                {group.logic}
              </button>
              <div className="h-px flex-1 bg-slate-700" />
            </div>
          )}
          <div className="space-y-1.5">
            {group.conditions.map((c) => {
              const isRangeOp = ["between", "not_between"].includes(c.operator);
              return (
                <div
                  key={c.id}
                  className="group flex items-center gap-2 rounded-lg border border-slate-700 bg-slate-800/50 px-3 py-2 transition-all hover:border-blue-500/50 hover:bg-slate-800"
                >
                  <GripVertical size={14} className="cursor-grab text-slate-600 hover:text-slate-400" />
                  <div className="h-2 w-2 rounded-full bg-blue-500" />
                  <IndicatorSelectorInline value={c.left} onChange={(v) => updateCondition(c.id, { left: v })} showNumber={false} />
                  <OperatorSelectorInline value={c.operator} onChange={(v) => updateCondition(c.id, { operator: v })} />
                  <IndicatorSelectorInline value={c.right} onChange={(v) => updateCondition(c.id, { right: v })} showNumber={true} />
                  {isRangeOp && (
                    <>
                      <span className="text-xs text-slate-500">and</span>
                      <IndicatorSelectorInline
                        value={c.right2 ?? { type: "number", value: 0 }}
                        onChange={(v) => updateCondition(c.id, { right2: v })}
                        showNumber={true}
                      />
                    </>
                  )}
                  <select
                    value={c.timeframe}
                    onChange={(e) => updateCondition(c.id, { timeframe: e.target.value })}
                    className="rounded border border-slate-600 bg-slate-700 px-2 py-0.5 text-[10px] font-medium text-slate-400"
                  >
                    {ADV_TIMEFRAMES.map((t) => (
                      <option key={t.value} value={t.value} className="bg-slate-800 text-slate-200">
                        {t.label}
                      </option>
                    ))}
                  </select>
                  <div className="flex-1" />
                  <div className="flex gap-0.5 opacity-0 transition-opacity group-hover:opacity-100">
                    <button onClick={() => duplicateCondition(c.id)} className="rounded p-1.5 hover:bg-slate-700" title="Duplicate">
                      <Files size={13} className="text-slate-500 hover:text-blue-400" />
                    </button>
                    <button
                      onClick={() => navigator.clipboard.writeText(JSON.stringify(c))}
                      className="rounded p-1.5 hover:bg-slate-700"
                      title="Copy"
                    >
                      <Copy size={13} className="text-slate-500 hover:text-blue-400" />
                    </button>
                    <button onClick={() => deleteCondition(c.id)} className="rounded p-1.5 hover:bg-slate-700" title="Delete">
                      <X size={13} className="text-slate-500 hover:text-red-400" />
                    </button>
                  </div>
                </div>
              );
            })}
          </div>
          <div className="flex gap-2">
            <button
              onClick={() => addCondition(group.id)}
              className="flex items-center gap-1 rounded-lg bg-blue-600 px-3 py-1.5 text-xs font-medium text-white transition-colors hover:bg-blue-500"
            >
              + Add condition
            </button>
            <button
              onClick={addGroup}
              className="flex items-center gap-1 rounded-lg border border-slate-600 bg-slate-700 px-3 py-1.5 text-xs font-medium text-slate-300 transition-colors hover:bg-slate-600"
            >
              + OR Group
            </button>
          </div>
        </div>
      ))}
    </div>
  );
}

export function ScreenerBuilder() {
  const [underlying, setUnderlying] = useState("NIFTY");
  const [timeframe, setTimeframe] = useState<"1m" | "5m" | "15m">("5m");
  const [indicator, setIndicator] = useState<"rsi_14" | "ema_20" | "macd">("rsi_14");
  const [operator, setOperator] = useState<">" | "<" | ">=" | "<=" | "==" | "crosses_above" | "crosses_below">(">");
  const [value, setValue] = useState(60);
  const [logic, setLogic] = useState<"AND" | "OR">("AND");
  const [results, setResults] = useState<ScanResult[]>([]);
  const [scanId, setScanId] = useState<string | null>(null);
  const [filter, setFilter] = useState("");
  const [sortBy, setSortBy] = useState<SortKey>("token");
  const [sortAsc, setSortAsc] = useState(true);
  const [page, setPage] = useState(1);
  const [selectedToken, setSelectedToken] = useState<string | null>(null);
  const [candles, setCandles] = useState<
    Array<{ timestamp: string; open: number; high: number; low: number; close: number }>
  >([]);
  const [instrumentCount, setInstrumentCount] = useState(0);
  const { userId } = useAuthActor();
  const effectiveUserId = userId ?? "user-1";
  const [screenerName, setScreenerName] = useState("My Screener");
  const [savedScreeners, setSavedScreeners] = useState<ScreenerPayload[]>([]);
  const [scanMode, setScanMode] = useState<"db" | "technical">("technical");
  const [technicalResults, setTechnicalResults] = useState<TechnicalScanResult[]>([]);
  const [technicalLoading, setTechnicalLoading] = useState(false);
  const [advancedGroups, setAdvancedGroups] = useState<FilterGroup[]>(DEFAULT_ADVANCED_GROUPS);
  const [magicFilter, setMagicFilter] = useState("");
  const [fyersConnected, setFyersConnected] = useState<boolean | null>(null);

  const pageSize = 10;

  useEffect(() => {
    fetchFyersStatus()
      .then((s) => setFyersConnected(s.authenticated ?? s.has_token))
      .catch(() => setFyersConnected(false));
  }, []);


  useEffect(() => {
    fetchInstruments()
      .then((rows) => setInstrumentCount(rows.length))
      .catch(() => setInstrumentCount(0));
  }, []);

  useEffect(() => {
    if (!scanId) return;
    const wsBase = (process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000").replace(
      "http",
      "ws"
    );
    const ws = new WebSocket(`${wsBase}/api/v1/ws/scan/${scanId}`);
    ws.onmessage = (evt) => {
      try {
        const msg = JSON.parse(evt.data) as { type?: string; payload?: unknown };
        if (msg.type === "scan_result" && msg.payload && typeof msg.payload === "object") {
          const payload = msg.payload as { results?: ScanResult[] };
          if (payload.results) setResults(payload.results);
        }
      } catch {
        // ignore
      }
    };
    return () => ws.close();
  }, [scanId]);

  async function refreshSavedScreeners() {
    const rows = await listScreeners(effectiveUserId);
    setSavedScreeners(rows);
  }

  async function onRunScan() {
    if (scanMode === "technical") {
      setTechnicalLoading(true);
      try {
        const hasConditions = advancedGroups.some((g) => g.conditions.length > 0);
        if (!hasConditions) {
          setTechnicalResults([]);
          return;
        }
        const filterConfig = groupsToFilterConfig(advancedGroups);
        const conditionTf = advancedGroups[0]?.conditions[0]?.timeframe ?? timeframe;
        const response = await runTechnicalScan({
          rules: [],
          filter_config: filterConfig,
          timeframe: conditionTf,
          max_strikes_per_underlying: 50,
        });
        setTechnicalResults(response.results);
        setPage(1);
      } finally {
        setTechnicalLoading(false);
      }
      return;
    }

    const groups: ScanGroup[] = [
      {
        logical_operator: logic,
        rules: [{ field: indicator, operator, value }],
      },
    ];
    const response = await runScan(
      { timeframe, underlying, groups },
      { actorId: effectiveUserId, alertUserId: effectiveUserId }
    );
    setScanId(response.scan_id);
    const persisted = await fetchScanResults(response.scan_id);
    setResults(persisted.results);
    setPage(1);
  }

  async function onSelectToken(token: string) {
    setSelectedToken(token);
    try {
      const chart = await fetchChart(token, timeframe, 200);
      setCandles(chart.candles);
    } catch {
      const c = await fetchStrikeCandles(token, timeframe, 200);
      setCandles(c);
    }
  }

  async function onSaveScreener() {
    const groups: ScanGroup[] = [
      {
        logical_operator: logic,
        rules: [{ field: indicator, operator, value }],
      },
    ];
    await createScreener({
      user_id: effectiveUserId,
      name: screenerName,
      underlying,
      timeframe,
      groups,
    });
    await refreshSavedScreeners();
  }

  async function onLoadScreener(screenerId: string) {
    const row = await getScreener(screenerId);
    setScreenerName(row.name);
    setTimeframe(row.timeframe);
    if (row.underlying) setUnderlying(row.underlying);
    if (row.groups.length > 0 && row.groups[0].rules.length > 0) {
      const firstRule = row.groups[0].rules[0];
      setLogic(row.groups[0].logical_operator);
      setIndicator(firstRule.field as "rsi_14" | "ema_20" | "macd");
      setOperator(firstRule.operator as ">" | "<" | "crosses_above" | "crosses_below");
      setValue(firstRule.value);
    }
  }

  const displayResults = scanMode === "technical" ? technicalResults : results;
  const filteredSorted = useMemo(() => {
    if (scanMode === "technical") {
      const techResults = displayResults as TechnicalScanResult[];
      const filtered = techResults.filter((r) =>
        r.symbol.toLowerCase().includes(filter.toLowerCase())
      );
      filtered.sort((a, b) =>
        sortAsc ? a.symbol.localeCompare(b.symbol) : b.symbol.localeCompare(a.symbol)
      );
      return filtered;
    }
    const filtered = (displayResults as ScanResult[]).filter((row) =>
      row.token.toLowerCase().includes(filter.toLowerCase())
    );
    filtered.sort((a, b) => {
      if (sortBy === "matched") {
        const av = (a as ScanResult).matched ? 1 : 0;
        const bv = (b as ScanResult).matched ? 1 : 0;
        return sortAsc ? av - bv : bv - av;
      }
      return sortAsc
        ? (a as ScanResult).token.localeCompare((b as ScanResult).token)
        : (b as ScanResult).token.localeCompare((a as ScanResult).token);
    });
    return filtered;
  }, [displayResults, filter, sortBy, sortAsc, scanMode]);

  const paged = filteredSorted.slice((page - 1) * pageSize, page * pageSize);
  const maxPage = Math.max(1, Math.ceil(filteredSorted.length / pageSize));

  return (
    <div className="min-h-screen w-full bg-slate-900 px-3 py-4">
      <div className="mx-auto max-w-7xl scale-[0.92] xl:scale-[0.95]" style={{ transformOrigin: "top center" }}>
        <section className="space-y-3">
          <Card className="border-slate-700 bg-slate-800/80">
            <div className="mb-3 flex items-center justify-between">
              <h2 className="text-base font-semibold text-slate-100">Screener Builder</h2>
              <span
                className={`rounded px-2 py-0.5 text-xs font-medium ${
                  fyersConnected === true
                    ? "bg-emerald-900/50 text-emerald-400"
                    : fyersConnected === false
                      ? "bg-amber-900/50 text-amber-400"
                      : "bg-slate-700 text-slate-500"
                }`}
                title={fyersConnected ? "Live data from Fyers API" : "Using DB - connect Fyers for live data"}
              >
                {fyersConnected === true ? "Fyers ✓" : fyersConnected === false ? "Fyers ○" : "..."}
              </span>
            </div>
            <p className="mb-3 text-xs text-slate-400">Instruments available: {instrumentCount}</p>
            <div className="mb-3 grid grid-cols-1 gap-2 md:grid-cols-4">
              <Input
                value={screenerName}
                onChange={(e) => setScreenerName(e.target.value)}
                placeholder="Screener name"
                className="border-slate-600 bg-slate-700/50 text-slate-200 placeholder-slate-500"
              />
              <Button
                variant="outline"
                onClick={() => void onSaveScreener()}
                className="border-slate-600 text-slate-300 hover:bg-slate-700 hover:text-slate-100"
              >
                Save Screener
              </Button>
              <Button
                variant="outline"
                onClick={() => void refreshSavedScreeners()}
                className="border-slate-600 text-slate-300 hover:bg-slate-700 hover:text-slate-100"
              >
                Load Saved List
              </Button>
            </div>

            <div className="mb-3 flex flex-wrap gap-2">
              <Button
                variant={scanMode === "technical" ? "default" : "outline"}
                size="sm"
                onClick={() => setScanMode("technical")}
                className={
                  scanMode === "technical"
                    ? "bg-blue-600 hover:bg-blue-500"
                    : "border-slate-600 text-slate-300 hover:bg-slate-700"
                }
              >
                Technical (Strike Charts)
              </Button>
              <Button
                variant={scanMode === "db" ? "default" : "outline"}
                size="sm"
                onClick={() => setScanMode("db")}
                className={
                  scanMode === "db"
                    ? "bg-blue-600 hover:bg-blue-500"
                    : "border-slate-600 text-slate-300 hover:bg-slate-700"
                }
              >
                DB Indicators
              </Button>
            </div>

            {scanMode === "technical" && (
              <div className="space-y-3 rounded-lg border border-slate-700 bg-slate-800/50 p-3">
                <div className="rounded-lg border border-slate-700 bg-slate-800/80 p-3">
                  <div className="mb-2 flex items-center gap-2">
                    <Sparkles size={16} className="text-amber-400" />
                    <span className="text-sm font-semibold text-slate-300">Magic Filters</span>
                    <Button
                      variant="outline"
                      size="sm"
                      className="ml-2 border-slate-600 text-xs text-slate-400 hover:bg-slate-700"
                      onClick={() => {
                        if (magicFilter.trim()) {
                          setAdvancedGroups((prev) =>
                            prev.map((g, i) => {
                              if (i > 0) return g;
                              const newCond = {
                                id: `${g.id}-${Date.now()}`,
                                left: { type: "indicator" as const, indicator: "RSI", params: { period: 14 }, offset: 0 },
                                operator: "gt",
                                right: { type: "number" as const, value: 60 },
                                timeframe: "15m",
                              };
                              return { ...g, conditions: [...g.conditions, newCond] };
                            })
                          );
                        }
                      }}
                    >
                      Append
                    </Button>
                    <Button
                      variant="outline"
                      size="sm"
                      className="border-slate-600 text-xs text-slate-400 hover:bg-slate-700"
                      onClick={() => {
                        if (magicFilter.trim()) {
                          setAdvancedGroups([
                            {
                              id: "1",
                              logic: "AND",
                              conditions: [
                                {
                                  id: `1-${Date.now()}`,
                                  left: { type: "indicator", indicator: "RSI", params: { period: 14 }, offset: 0 },
                                  operator: "gt",
                                  right: { type: "number", value: 60 },
                                  timeframe: "15m",
                                },
                              ],
                            },
                          ]);
                        }
                      }}
                    >
                      Replace
                    </Button>
                  </div>
                  <Input
                    value={magicFilter}
                    onChange={(e) => setMagicFilter(e.target.value)}
                    placeholder="Type: 'RSI crosses above 60' or 'MACD bullish crossover on 15min'"
                    className="border-slate-600 bg-slate-700/50 text-sm text-slate-200 placeholder-slate-500"
                  />
                </div>
                <AdvancedFilterPanelInline
                  groups={advancedGroups}
                  setGroups={setAdvancedGroups}
                />
              </div>
            )}

            {scanMode === "db" && (
              <div className="grid grid-cols-1 gap-2 md:grid-cols-6">
                <Select
                  value={underlying}
                  onChange={(e) => setUnderlying(e.target.value)}
                  className="border-slate-600 bg-slate-700/50 text-slate-200"
                >
                  <option value="NIFTY">NIFTY</option>
                  <option value="BANKNIFTY">BANKNIFTY</option>
                  <option value="FINNIFTY">FINNIFTY</option>
                </Select>
                <Select
                  value={timeframe}
                  onChange={(e) => setTimeframe(e.target.value as "1m" | "5m" | "15m")}
                  className="border-slate-600 bg-slate-700/50 text-slate-200"
                >
                  <option value="1m">1m</option>
                  <option value="5m">5m</option>
                  <option value="15m">15m</option>
                </Select>
                <Select
                  value={indicator}
                  onChange={(e) => setIndicator(e.target.value as "rsi_14" | "ema_20" | "macd")}
                  className="border-slate-600 bg-slate-700/50 text-slate-200"
                >
                  <option value="rsi_14">RSI 14</option>
                  <option value="ema_20">EMA 20</option>
                  <option value="macd">MACD</option>
                </Select>
                <Select
                  value={operator}
                  onChange={(e) =>
                    setOperator(e.target.value as ">" | "<" | "crosses_above" | "crosses_below")
                  }
                  className="border-slate-600 bg-slate-700/50 text-slate-200"
                >
                  <option value=">">{">"}</option>
                  <option value="<">{"<"}</option>
                  <option value="crosses_above">crosses above</option>
                  <option value="crosses_below">crosses below</option>
                </Select>
                <Select
                  value={logic}
                  onChange={(e) => setLogic(e.target.value as "AND" | "OR")}
                  className="border-slate-600 bg-slate-700/50 text-slate-200"
                >
                  <option value="AND">AND group</option>
                  <option value="OR">OR group</option>
                </Select>
                <Input
                  type="number"
                  value={value}
                  onChange={(e) => setValue(Number(e.target.value))}
                  className="border-slate-600 bg-slate-700/50 text-slate-200"
                />
              </div>
            )}

            <div className="mt-4 flex flex-wrap gap-2 border-t border-slate-700 pt-4">
              <Button
                onClick={onRunScan}
                className="bg-green-600 hover:bg-green-500"
                disabled={technicalLoading}
              >
                <Play size={14} className="mr-2" />
                {technicalLoading ? "Scanning..." : "Run Scan"}
              </Button>
              <Button
                variant="outline"
                onClick={() => void onSaveScreener()}
                className="border-slate-600 text-slate-300 hover:bg-slate-700"
              >
                Save
              </Button>
              <Button
                variant="outline"
                className="border-amber-700/50 text-amber-400 hover:bg-amber-900/30"
              >
                <History size={14} className="mr-2" />
                Backtest
              </Button>
              <Button
                variant="outline"
                className="border-blue-700/50 text-blue-400 hover:bg-blue-900/30"
              >
                <Bell size={14} className="mr-2" />
                Alert
              </Button>
              <Button variant="outline" className="border-slate-600 text-slate-400 hover:bg-slate-700">
                <MoreHorizontal size={14} className="mr-2" />
                More
              </Button>
            </div>
          </Card>

          <Card className="border-slate-700 bg-slate-800/80">
            <h3 className="mb-2 text-sm font-semibold text-slate-100">Saved Screeners</h3>
            <ul className="space-y-1.5 text-sm text-slate-300">
              {savedScreeners.map((row) => (
                <li
                  key={row.id}
                  className="flex items-center justify-between rounded border border-slate-700 p-2"
                >
                  <span>
                    {row.name} ({row.timeframe})
                  </span>
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={() => void onLoadScreener(row.id)}
                    className="border-slate-600 text-slate-300 hover:bg-slate-700"
                  >
                    Load
                  </Button>
                </li>
              ))}
              {savedScreeners.length === 0 ? (
                <li className="text-xs text-slate-500">No saved screeners yet.</li>
              ) : null}
            </ul>
          </Card>

          <Card className="border-slate-700 bg-slate-800/80">
            <div className="mb-2 flex flex-col gap-1">
              <div className="flex items-center justify-between">
                <h3 className="text-sm font-semibold text-slate-100">Results</h3>
                <Input
                value={filter}
                onChange={(e) => setFilter(e.target.value)}
                placeholder="Filter token"
                className="max-w-48 border-slate-600 bg-slate-700/50 text-xs text-slate-200 placeholder-slate-500"
              />
              </div>
              {scanMode === "technical" && technicalLoading === false && filteredSorted.length === 0 ? (
                <p className="text-xs text-amber-400">
                  No matches. Only strikes with enough history for your condition are included. Ensure Fyers is connected (green badge).
                </p>
              ) : null}
            </div>
            <div className="overflow-x-auto">
              <Table>
                <TableHead>
                  <tr>
                    <th
                      className="cursor-pointer py-1.5 text-xs"
                      onClick={() => {
                        setSortBy("token");
                        setSortAsc((v) => !v);
                      }}
                    >
                      {scanMode === "technical" ? "Symbol" : "Token"}
                    </th>
                    {scanMode === "technical" ? (
                      <>
                        <th className="py-1.5 text-xs">Strike</th>
                        <th className="py-1.5 text-xs">Expiry</th>
                        <th className="py-1.5 text-xs">LTP</th>
                        <th className="py-1.5 text-xs">RSI</th>
                        <th className="py-1.5 text-xs">MACD</th>
                        <th className="py-1.5 text-xs">EMA20</th>
                      </>
                    ) : (
                      <>
                        <th
                          className="cursor-pointer py-1.5 text-xs"
                          onClick={() => {
                            setSortBy("matched");
                            setSortAsc((v) => !v);
                          }}
                        >
                          Matched
                        </th>
                        <th className="py-1.5 text-xs">Reason</th>
                      </>
                    )}
                  </tr>
                </TableHead>
                <TableBody>
                  {scanMode === "technical"
                    ? paged.map((row) => (
                        <tr
                          key={(row as TechnicalScanResult).symbol}
                          className="cursor-pointer border-t border-slate-700 hover:bg-slate-700/50"
                          onClick={() =>
                            onSelectToken((row as TechnicalScanResult).symbol)
                          }
                        >
                          <td className="py-1.5 text-xs text-slate-100">
                            {(row as TechnicalScanResult).symbol}
                          </td>
                          <td className="py-1.5 text-xs text-slate-300">
                            {(row as TechnicalScanResult).strike_price ?? "-"}
                          </td>
                          <td className="py-1.5 text-xs text-slate-400">
                            {(row as TechnicalScanResult).expiry ?? "-"}
                          </td>
                          <td className="py-1.5 text-xs text-emerald-300">
                            {(row as TechnicalScanResult).ltp?.toFixed(2) ?? "-"}
                          </td>
                          <td className="py-1.5 text-xs text-slate-300">
                            {(row as TechnicalScanResult).indicators?.rsi_14?.toFixed(2) ?? "-"}
                          </td>
                          <td className="py-1.5 text-xs text-slate-300">
                            {(row as TechnicalScanResult).indicators?.macd?.toFixed(3) ?? "-"}
                          </td>
                          <td className="py-1.5 text-xs text-slate-300">
                            {(row as TechnicalScanResult).indicators?.ema_20?.toFixed(2) ?? "-"}
                          </td>
                        </tr>
                      ))
                    : paged.map((row) => (
                        <tr
                          key={(row as ScanResult).token}
                          className="cursor-pointer border-t border-slate-700 hover:bg-slate-700/50"
                          onClick={() => onSelectToken((row as ScanResult).token)}
                        >
                          <td className="py-1.5 text-xs text-slate-100">
                            {(row as ScanResult).token}
                          </td>
                          <td
                            className={`py-1.5 text-xs ${
                              (row as ScanResult).matched
                                ? "text-emerald-400"
                                : "text-rose-400"
                            }`}
                          >
                            {(row as ScanResult).matched ? "Yes" : "No"}
                          </td>
                          <td className="py-1.5 text-xs text-slate-300">
                            {(row as ScanResult).reason}
                          </td>
                        </tr>
                      ))}
                </TableBody>
              </Table>
            </div>
            <div className="mt-2 flex items-center justify-end gap-2 text-xs text-slate-400">
              <Button
                variant="outline"
                size="sm"
                disabled={page <= 1}
                onClick={() => setPage((p) => p - 1)}
                className="border-slate-600 text-slate-300 hover:bg-slate-700"
              >
                Prev
              </Button>
              <span>
                Page {page} / {maxPage}
              </span>
              <Button
                variant="outline"
                size="sm"
                disabled={page >= maxPage}
                onClick={() => setPage((p) => p + 1)}
                className="border-slate-600 text-slate-300 hover:bg-slate-700"
              >
                Next
              </Button>
            </div>
          </Card>

          {selectedToken ? (
            <ChartPopup
              token={selectedToken}
              candles={candles}
              onClose={() => setSelectedToken(null)}
            />
          ) : null}
        </section>
      </div>
    </div>
  );
}
