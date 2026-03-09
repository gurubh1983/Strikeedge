// StrikeEdge Filter Builder - Blue/Teal Theme (Matching App)
// File: frontend/web/src/app/screener/FilterBuilder.tsx

"use client";

import React, { useState, useRef, useEffect } from 'react';
import { 
  Settings2, 
  Copy, 
  Files, 
  Eye, 
  X, 
  Plus,
  Play,
  Save,
  History,
  Bell,
  MoreHorizontal,
  Sparkles,
  ChevronDown,
  GripVertical,
  Search
} from 'lucide-react';

// ============================================
// TYPES
// ============================================

interface IndicatorValue {
  type: 'indicator' | 'number';
  indicator?: string;
  params?: Record<string, number>;
  value?: number;
}

interface FilterCondition {
  id: string;
  left: IndicatorValue;
  operator: string;
  right: IndicatorValue;
  timeframe: string;
}

interface FilterGroup {
  id: string;
  logic: 'AND' | 'OR';
  conditions: FilterCondition[];
}

// ============================================
// INDICATOR DEFINITIONS
// ============================================

interface IndicatorDef {
  code: string;
  name: string;
  category: string;
  params: { name: string; default: number; min: number; max: number }[];
  format: (params: Record<string, number>) => string;
}

const INDICATORS: IndicatorDef[] = [
  // Price
  { code: 'OPEN', name: 'Open', category: 'Price', params: [], format: () => 'Open' },
  { code: 'HIGH', name: 'High', category: 'Price', params: [], format: () => 'High' },
  { code: 'LOW', name: 'Low', category: 'Price', params: [], format: () => 'Low' },
  { code: 'CLOSE', name: 'Close', category: 'Price', params: [], format: () => 'Close' },
  { code: 'VWAP', name: 'VWAP', category: 'Price', params: [], format: () => 'VWAP' },
  
  // Moving Averages
  { code: 'SMA', name: 'SMA', category: 'Moving Averages', 
    params: [{ name: 'period', default: 20, min: 1, max: 500 }],
    format: (p) => `SMA(${p.period})` },
  { code: 'EMA', name: 'EMA', category: 'Moving Averages',
    params: [{ name: 'period', default: 20, min: 1, max: 500 }],
    format: (p) => `EMA(${p.period})` },
  { code: 'WMA', name: 'WMA', category: 'Moving Averages',
    params: [{ name: 'period', default: 20, min: 1, max: 500 }],
    format: (p) => `WMA(${p.period})` },
  { code: 'DEMA', name: 'DEMA', category: 'Moving Averages',
    params: [{ name: 'period', default: 20, min: 1, max: 500 }],
    format: (p) => `DEMA(${p.period})` },
  { code: 'TEMA', name: 'TEMA', category: 'Moving Averages',
    params: [{ name: 'period', default: 20, min: 1, max: 500 }],
    format: (p) => `TEMA(${p.period})` },
  { code: 'HMA', name: 'Hull MA', category: 'Moving Averages',
    params: [{ name: 'period', default: 20, min: 1, max: 500 }],
    format: (p) => `HMA(${p.period})` },
  
  // RSI
  { code: 'RSI', name: 'RSI', category: 'Momentum',
    params: [{ name: 'period', default: 14, min: 2, max: 100 }],
    format: (p) => `RSI(${p.period})` },
  { code: 'RSI_SMA', name: 'RSI SMA', category: 'Momentum',
    params: [
      { name: 'rsi_period', default: 14, min: 2, max: 100 },
      { name: 'sma_period', default: 14, min: 1, max: 100 }
    ],
    format: (p) => `RSI(${p.rsi_period}) SMA(${p.sma_period})` },
  
  // Stochastic
  { code: 'STOCH_K', name: 'Stochastic %K', category: 'Momentum',
    params: [
      { name: 'k_period', default: 14, min: 1, max: 100 },
      { name: 'smooth', default: 3, min: 1, max: 50 }
    ],
    format: (p) => `%K(${p.k_period},${p.smooth})` },
  { code: 'STOCH_D', name: 'Stochastic %D', category: 'Momentum',
    params: [
      { name: 'k_period', default: 14, min: 1, max: 100 },
      { name: 'd_period', default: 3, min: 1, max: 50 }
    ],
    format: (p) => `%D(${p.k_period},${p.d_period})` },
  
  // Other Momentum
  { code: 'CCI', name: 'CCI', category: 'Momentum',
    params: [{ name: 'period', default: 20, min: 1, max: 100 }],
    format: (p) => `CCI(${p.period})` },
  { code: 'WILLR', name: 'Williams %R', category: 'Momentum',
    params: [{ name: 'period', default: 14, min: 1, max: 100 }],
    format: (p) => `W%R(${p.period})` },
  { code: 'MFI', name: 'MFI', category: 'Momentum',
    params: [{ name: 'period', default: 14, min: 1, max: 100 }],
    format: (p) => `MFI(${p.period})` },
  { code: 'ROC', name: 'ROC', category: 'Momentum',
    params: [{ name: 'period', default: 10, min: 1, max: 100 }],
    format: (p) => `ROC(${p.period})` },
  
  // MACD
  { code: 'MACD', name: 'MACD Line', category: 'Trend',
    params: [
      { name: 'fast', default: 12, min: 1, max: 100 },
      { name: 'slow', default: 26, min: 1, max: 100 }
    ],
    format: (p) => `MACD(${p.fast},${p.slow})` },
  { code: 'MACD_SIGNAL', name: 'MACD Signal', category: 'Trend',
    params: [
      { name: 'fast', default: 12, min: 1, max: 100 },
      { name: 'slow', default: 26, min: 1, max: 100 },
      { name: 'signal', default: 9, min: 1, max: 50 }
    ],
    format: (p) => `Signal(${p.fast},${p.slow},${p.signal})` },
  { code: 'MACD_HIST', name: 'MACD Histogram', category: 'Trend',
    params: [
      { name: 'fast', default: 12, min: 1, max: 100 },
      { name: 'slow', default: 26, min: 1, max: 100 },
      { name: 'signal', default: 9, min: 1, max: 50 }
    ],
    format: (p) => `Hist(${p.fast},${p.slow},${p.signal})` },
  
  // ADX
  { code: 'ADX', name: 'ADX', category: 'Trend',
    params: [{ name: 'period', default: 14, min: 1, max: 100 }],
    format: (p) => `ADX(${p.period})` },
  { code: 'PLUS_DI', name: '+DI', category: 'Trend',
    params: [{ name: 'period', default: 14, min: 1, max: 100 }],
    format: (p) => `+DI(${p.period})` },
  { code: 'MINUS_DI', name: '-DI', category: 'Trend',
    params: [{ name: 'period', default: 14, min: 1, max: 100 }],
    format: (p) => `-DI(${p.period})` },
  
  // Supertrend
  { code: 'SUPERTREND', name: 'Supertrend', category: 'Trend',
    params: [
      { name: 'period', default: 10, min: 1, max: 100 },
      { name: 'multiplier', default: 3, min: 1, max: 10 }
    ],
    format: (p) => `ST(${p.period},${p.multiplier})` },
  
  // Volatility
  { code: 'ATR', name: 'ATR', category: 'Volatility',
    params: [{ name: 'period', default: 14, min: 1, max: 100 }],
    format: (p) => `ATR(${p.period})` },
  { code: 'BB_UPPER', name: 'BB Upper', category: 'Volatility',
    params: [
      { name: 'period', default: 20, min: 1, max: 100 },
      { name: 'std', default: 2, min: 1, max: 5 }
    ],
    format: (p) => `BBU(${p.period},${p.std})` },
  { code: 'BB_MIDDLE', name: 'BB Middle', category: 'Volatility',
    params: [{ name: 'period', default: 20, min: 1, max: 100 }],
    format: (p) => `BBM(${p.period})` },
  { code: 'BB_LOWER', name: 'BB Lower', category: 'Volatility',
    params: [
      { name: 'period', default: 20, min: 1, max: 100 },
      { name: 'std', default: 2, min: 1, max: 5 }
    ],
    format: (p) => `BBL(${p.period},${p.std})` },
  { code: 'BB_PERCENT_B', name: 'BB %B', category: 'Volatility',
    params: [
      { name: 'period', default: 20, min: 1, max: 100 },
      { name: 'std', default: 2, min: 1, max: 5 }
    ],
    format: (p) => `%B(${p.period},${p.std})` },
  
  // Volume
  { code: 'VOLUME', name: 'Volume', category: 'Volume', params: [], format: () => 'Volume' },
  { code: 'VOLUME_SMA', name: 'Volume SMA', category: 'Volume',
    params: [{ name: 'period', default: 20, min: 1, max: 100 }],
    format: (p) => `Vol SMA(${p.period})` },
  { code: 'OBV', name: 'OBV', category: 'Volume', params: [], format: () => 'OBV' },
  
  // Candlestick Patterns
  { code: 'DOJI', name: 'Doji', category: 'Candlestick', params: [], format: () => 'Doji' },
  { code: 'HAMMER', name: 'Hammer', category: 'Candlestick', params: [], format: () => 'Hammer' },
  { code: 'INVERTED_HAMMER', name: 'Inverted Hammer', category: 'Candlestick', params: [], format: () => 'Inv Hammer' },
  { code: 'BULLISH_ENGULFING', name: 'Bullish Engulfing', category: 'Candlestick', params: [], format: () => 'Bull Engulf' },
  { code: 'BEARISH_ENGULFING', name: 'Bearish Engulfing', category: 'Candlestick', params: [], format: () => 'Bear Engulf' },
  { code: 'MORNING_STAR', name: 'Morning Star', category: 'Candlestick', params: [], format: () => 'Morning Star' },
  { code: 'EVENING_STAR', name: 'Evening Star', category: 'Candlestick', params: [], format: () => 'Evening Star' },
  { code: 'THREE_WHITE_SOLDIERS', name: '3 White Soldiers', category: 'Candlestick', params: [], format: () => '3 White' },
  { code: 'THREE_BLACK_CROWS', name: '3 Black Crows', category: 'Candlestick', params: [], format: () => '3 Black' },
  { code: 'SHOOTING_STAR', name: 'Shooting Star', category: 'Candlestick', params: [], format: () => 'Shoot Star' },
  
  // Price Action
  { code: 'PREV_DAY_HIGH', name: 'Prev Day High', category: 'Price Action', params: [], format: () => 'PDH' },
  { code: 'PREV_DAY_LOW', name: 'Prev Day Low', category: 'Price Action', params: [], format: () => 'PDL' },
  { code: 'PREV_DAY_CLOSE', name: 'Prev Day Close', category: 'Price Action', params: [], format: () => 'PDC' },
  { code: 'DAY_CHANGE_PCT', name: 'Day Change %', category: 'Price Action', params: [], format: () => 'Chg%' },
  { code: 'GAP_PCT', name: 'Gap %', category: 'Price Action', params: [], format: () => 'Gap%' },
  { code: 'HIGH_OF_N', name: 'High of N', category: 'Price Action',
    params: [{ name: 'period', default: 20, min: 1, max: 252 }],
    format: (p) => `High(${p.period})` },
  { code: 'LOW_OF_N', name: 'Low of N', category: 'Price Action',
    params: [{ name: 'period', default: 20, min: 1, max: 252 }],
    format: (p) => `Low(${p.period})` },
  
  // Options
  { code: 'DELTA', name: 'Delta', category: 'Options', params: [], format: () => 'Delta' },
  { code: 'GAMMA', name: 'Gamma', category: 'Options', params: [], format: () => 'Gamma' },
  { code: 'THETA', name: 'Theta', category: 'Options', params: [], format: () => 'Theta' },
  { code: 'VEGA', name: 'Vega', category: 'Options', params: [], format: () => 'Vega' },
  { code: 'IV', name: 'IV', category: 'Options', params: [], format: () => 'IV' },
  { code: 'IV_RANK', name: 'IV Rank', category: 'Options', params: [], format: () => 'IV Rank' },
  { code: 'OI', name: 'Open Interest', category: 'Options', params: [], format: () => 'OI' },
  { code: 'OI_CHANGE', name: 'OI Change', category: 'Options', params: [], format: () => 'OI Chg' },
  { code: 'OI_CHANGE_PCT', name: 'OI Change %', category: 'Options', params: [], format: () => 'OI Chg%' },
  { code: 'PCR', name: 'Put Call Ratio', category: 'Options', params: [], format: () => 'PCR' },
  { code: 'VOLUME_OI_RATIO', name: 'Volume/OI', category: 'Options', params: [], format: () => 'Vol/OI' },
];

const OPERATORS = [
  { value: 'gt', label: '>', fullLabel: 'Greater Than' },
  { value: 'gte', label: '≥', fullLabel: 'Greater or Equal' },
  { value: 'lt', label: '<', fullLabel: 'Less Than' },
  { value: 'lte', label: '≤', fullLabel: 'Less or Equal' },
  { value: 'eq', label: '=', fullLabel: 'Equals' },
  { value: 'neq', label: '≠', fullLabel: 'Not Equals' },
  { value: 'crosses_above', label: '⬆', fullLabel: 'Crosses Above' },
  { value: 'crosses_below', label: '⬇', fullLabel: 'Crosses Below' },
];

const TIMEFRAMES = [
  { value: '1m', label: '1m' },
  { value: '3m', label: '3m' },
  { value: '5m', label: '5m' },
  { value: '15m', label: '15m' },
  { value: '30m', label: '30m' },
  { value: '1h', label: '1H' },
  { value: '4h', label: '4H' },
  { value: '1d', label: 'D' },
  { value: '1w', label: 'W' },
];

const SEGMENTS = [
  { value: 'nifty_options', label: 'NIFTY Options' },
  { value: 'banknifty_options', label: 'BANKNIFTY Options' },
  { value: 'finnifty_options', label: 'FINNIFTY Options' },
  { value: 'stock_options', label: 'Stock Options' },
  { value: 'all_fo', label: 'All F&O' },
];

// ============================================
// INDICATOR SELECTOR COMPONENT
// ============================================

interface IndicatorSelectorProps {
  value: IndicatorValue;
  onChange: (value: IndicatorValue) => void;
  showNumber?: boolean;
}

function IndicatorSelector({ value, onChange, showNumber = true }: IndicatorSelectorProps) {
  const [showPicker, setShowPicker] = useState(false);
  const [search, setSearch] = useState('');
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (ref.current && !ref.current.contains(e.target as Node)) {
        setShowPicker(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const indicator = value.type === 'indicator' 
    ? INDICATORS.find(i => i.code === value.indicator) 
    : null;

  const categories = [...new Set(INDICATORS.map(i => i.category))];

  const filteredIndicators = INDICATORS.filter(i =>
    i.name.toLowerCase().includes(search.toLowerCase()) ||
    i.code.toLowerCase().includes(search.toLowerCase())
  );

  const handleSelectIndicator = (ind: IndicatorDef) => {
    const defaultParams: Record<string, number> = {};
    ind.params.forEach(p => {
      defaultParams[p.name] = p.default;
    });
    onChange({
      type: 'indicator',
      indicator: ind.code,
      params: defaultParams
    });
    setShowPicker(false);
  };

  const handleParamChange = (paramName: string, newValue: number) => {
    if (value.type === 'indicator') {
      onChange({
        ...value,
        params: { ...value.params, [paramName]: newValue }
      });
    }
  };

  return (
    <div className="relative inline-flex items-center gap-0.5" ref={ref}>
      {value.type === 'indicator' && indicator ? (
        <div className="flex items-center bg-slate-100 border border-slate-300 rounded px-1.5 py-0.5">
          <span 
            className="text-slate-700 text-xs font-medium cursor-pointer hover:text-teal-600 px-0.5"
            onClick={() => setShowPicker(true)}
          >
            {indicator.name}
          </span>
          {indicator.params.length > 0 && (
            <>
              <span className="text-slate-400 text-xs">(</span>
              {indicator.params.map((param, idx) => (
                <React.Fragment key={param.name}>
                  <input
                    type="number"
                    value={value.params?.[param.name] || param.default}
                    onChange={(e) => handleParamChange(param.name, parseInt(e.target.value) || param.default)}
                    className="w-7 text-center bg-teal-600 text-white rounded text-xs font-bold mx-0.5 focus:outline-none focus:ring-1 focus:ring-teal-400 [appearance:textfield] [&::-webkit-outer-spin-button]:appearance-none [&::-webkit-inner-spin-button]:appearance-none"
                    min={param.min}
                    max={param.max}
                  />
                  {idx < indicator.params.length - 1 && <span className="text-slate-400 text-xs">,</span>}
                </React.Fragment>
              ))}
              <span className="text-slate-400 text-xs">)</span>
            </>
          )}
        </div>
      ) : value.type === 'number' ? (
        <input
          type="number"
          value={value.value || 0}
          onChange={(e) => onChange({ type: 'number', value: parseFloat(e.target.value) || 0 })}
          className="w-14 text-center bg-teal-600 text-white rounded text-xs font-bold px-2 py-1 focus:outline-none focus:ring-1 focus:ring-teal-400 [appearance:textfield] [&::-webkit-outer-spin-button]:appearance-none [&::-webkit-inner-spin-button]:appearance-none"
        />
      ) : (
        <button
          onClick={() => setShowPicker(true)}
          className="text-xs text-teal-600 hover:text-teal-700 px-2 py-1 border border-teal-300 rounded hover:bg-teal-50"
        >
          Select...
        </button>
      )}

      <button
        onClick={() => setShowPicker(!showPicker)}
        className="p-0.5 text-slate-400 hover:text-teal-600"
      >
        <ChevronDown size={12} />
      </button>

      {showPicker && (
        <div className="absolute top-full left-0 mt-1 w-64 bg-white border border-slate-200 rounded-lg shadow-xl z-50 overflow-hidden">
          <div className="p-2 border-b bg-slate-50">
            <div className="relative">
              <Search size={14} className="absolute left-2 top-1/2 -translate-y-1/2 text-slate-400" />
              <input
                type="text"
                placeholder="Search indicators..."
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                className="w-full pl-7 pr-2 py-1.5 text-xs border border-slate-200 rounded focus:outline-none focus:ring-1 focus:ring-teal-400"
                autoFocus
              />
            </div>
          </div>

          {showNumber && (
            <div
              onClick={() => {
                onChange({ type: 'number', value: 0 });
                setShowPicker(false);
              }}
              className="px-3 py-2 text-xs cursor-pointer hover:bg-teal-50 border-b font-medium text-teal-700 flex items-center gap-2"
            >
              <span className="text-base">🔢</span> Enter Number Value
            </div>
          )}

          <div className="max-h-64 overflow-y-auto">
            {categories.map(category => {
              const items = filteredIndicators.filter(i => i.category === category);
              if (items.length === 0) return null;
              return (
                <div key={category}>
                  <div className="px-2 py-1.5 bg-slate-100 text-[10px] font-semibold text-slate-500 uppercase tracking-wider sticky top-0">
                    {category}
                  </div>
                  {items.map(ind => (
                    <div
                      key={ind.code}
                      onClick={() => handleSelectIndicator(ind)}
                      className={`px-3 py-1.5 text-xs cursor-pointer hover:bg-teal-50 ${
                        value.indicator === ind.code ? 'bg-teal-100 text-teal-700' : 'text-slate-700'
                      }`}
                    >
                      {ind.name}
                      {ind.params.length > 0 && (
                        <span className="text-slate-400 ml-1">
                          ({ind.params.map(p => p.default).join(',')})
                        </span>
                      )}
                    </div>
                  ))}
                </div>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
}

// ============================================
// FILTER ROW COMPONENT
// ============================================

interface FilterRowProps {
  condition: FilterCondition;
  onUpdate: (id: string, updates: Partial<FilterCondition>) => void;
  onDelete: (id: string) => void;
  onDuplicate: (id: string) => void;
}

function FilterRow({ condition, onUpdate, onDelete, onDuplicate }: FilterRowProps) {
  const [showOperatorDropdown, setShowOperatorDropdown] = useState(false);
  const [showTimeframeDropdown, setShowTimeframeDropdown] = useState(false);

  return (
    <div className="filter-row flex items-center gap-1.5 py-2 px-3 bg-white border border-slate-200 rounded-lg hover:border-teal-300 hover:shadow-sm transition-all group">
      {/* Drag Handle */}
      <div className="cursor-grab text-slate-300 hover:text-slate-500">
        <GripVertical size={14} />
      </div>

      {/* Bullet */}
      <div className="w-2 h-2 rounded-full bg-teal-500" />

      {/* LEFT Indicator */}
      <IndicatorSelector
        value={condition.left}
        onChange={(v) => onUpdate(condition.id, { left: v })}
        showNumber={false}
      />

      {/* OPERATOR */}
      <div className="relative">
        <button
          onClick={() => setShowOperatorDropdown(!showOperatorDropdown)}
          className="px-2 py-1 text-xs font-bold text-amber-700 bg-amber-50 border border-amber-200 rounded hover:bg-amber-100 min-w-[28px]"
        >
          {OPERATORS.find(o => o.value === condition.operator)?.label || '>'}
        </button>
        {showOperatorDropdown && (
          <div className="absolute top-full left-1/2 -translate-x-1/2 mt-1 w-40 bg-white border border-slate-200 rounded-lg shadow-lg z-50 py-1">
            {OPERATORS.map(op => (
              <div
                key={op.value}
                onClick={() => {
                  onUpdate(condition.id, { operator: op.value });
                  setShowOperatorDropdown(false);
                }}
                className={`px-3 py-1.5 text-xs cursor-pointer hover:bg-teal-50 flex items-center gap-2 ${
                  condition.operator === op.value ? 'bg-teal-100' : ''
                }`}
              >
                <span className="font-bold text-amber-600 w-5">{op.label}</span>
                <span className="text-slate-600">{op.fullLabel}</span>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* RIGHT Indicator/Value */}
      <IndicatorSelector
        value={condition.right}
        onChange={(v) => onUpdate(condition.id, { right: v })}
        showNumber={true}
      />

      {/* TIMEFRAME */}
      <div className="relative">
        <button
          onClick={() => setShowTimeframeDropdown(!showTimeframeDropdown)}
          className="px-2 py-1 text-[10px] font-semibold text-slate-600 bg-slate-100 border border-slate-200 rounded hover:bg-slate-200"
        >
          {TIMEFRAMES.find(t => t.value === condition.timeframe)?.label || 'D'}
        </button>
        {showTimeframeDropdown && (
          <div className="absolute top-full right-0 mt-1 w-20 bg-white border border-slate-200 rounded-lg shadow-lg z-50 py-1">
            {TIMEFRAMES.map(tf => (
              <div
                key={tf.value}
                onClick={() => {
                  onUpdate(condition.id, { timeframe: tf.value });
                  setShowTimeframeDropdown(false);
                }}
                className={`px-3 py-1.5 text-xs cursor-pointer hover:bg-teal-50 text-center ${
                  condition.timeframe === tf.value ? 'bg-teal-100 text-teal-700 font-medium' : 'text-slate-600'
                }`}
              >
                {tf.label}
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Spacer */}
      <div className="flex-1" />

      {/* Actions */}
      <div className="flex items-center gap-0.5 opacity-0 group-hover:opacity-100 transition-opacity">
        <button onClick={() => onDuplicate(condition.id)} className="p-1.5 hover:bg-slate-100 rounded" title="Duplicate">
          <Files size={13} className="text-slate-400 hover:text-teal-600" />
        </button>
        <button onClick={() => navigator.clipboard.writeText(JSON.stringify(condition))} className="p-1.5 hover:bg-slate-100 rounded" title="Copy">
          <Copy size={13} className="text-slate-400 hover:text-teal-600" />
        </button>
        <button onClick={() => onDelete(condition.id)} className="p-1.5 hover:bg-red-50 rounded" title="Delete">
          <X size={13} className="text-slate-400 hover:text-red-500" />
        </button>
      </div>
    </div>
  );
}

// ============================================
// MAIN FILTER BUILDER
// ============================================

export default function FilterBuilder() {
  const [segment, setSegment] = useState('nifty_options');
  const [groups, setGroups] = useState<FilterGroup[]>([
    {
      id: '1',
      logic: 'AND',
      conditions: [
        {
          id: '1-1',
          left: { type: 'indicator', indicator: 'RSI', params: { period: 14 } },
          operator: 'gt',
          right: { type: 'indicator', indicator: 'RSI_SMA', params: { rsi_period: 14, sma_period: 14 } },
          timeframe: '1d',
        },
        {
          id: '1-2',
          left: { type: 'indicator', indicator: 'CLOSE', params: {} },
          operator: 'gt',
          right: { type: 'indicator', indicator: 'EMA', params: { period: 20 } },
          timeframe: '1d',
        }
      ]
    }
  ]);
  const [magicFilter, setMagicFilter] = useState('');
  const [isScanning, setIsScanning] = useState(false);
  const [results, setResults] = useState<any[]>([]);

  const addCondition = (groupId: string) => {
    setGroups(groups.map(g => {
      if (g.id === groupId) {
        return {
          ...g,
          conditions: [
            ...g.conditions,
            {
              id: `${groupId}-${Date.now()}`,
              left: { type: 'indicator', indicator: 'RSI', params: { period: 14 } },
              operator: 'gt',
              right: { type: 'number', value: 60 },
              timeframe: '1d',
            }
          ]
        };
      }
      return g;
    }));
  };

  const addGroup = () => {
    setGroups([
      ...groups,
      { id: Date.now().toString(), logic: 'OR', conditions: [] }
    ]);
  };

  const updateCondition = (conditionId: string, updates: Partial<FilterCondition>) => {
    setGroups(groups.map(g => ({
      ...g,
      conditions: g.conditions.map(c =>
        c.id === conditionId ? { ...c, ...updates } : c
      )
    })));
  };

  const deleteCondition = (conditionId: string) => {
    setGroups(groups.map(g => ({
      ...g,
      conditions: g.conditions.filter(c => c.id !== conditionId)
    })));
  };

  const duplicateCondition = (conditionId: string) => {
    setGroups(groups.map(g => {
      const idx = g.conditions.findIndex(c => c.id === conditionId);
      if (idx === -1) return g;
      const newCond = { ...g.conditions[idx], id: `${g.id}-${Date.now()}` };
      return {
        ...g,
        conditions: [...g.conditions.slice(0, idx + 1), newCond, ...g.conditions.slice(idx + 1)]
      };
    }));
  };

  const runScan = async () => {
    setIsScanning(true);
    setResults([]);
    try {
      const response = await fetch('/api/v1/scanner/technical', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ segment, groups })
      });
      const data = await response.json();
      setResults(data.results || []);
    } catch (error) {
      console.error('Scan failed:', error);
    } finally {
      setIsScanning(false);
    }
  };

  return (
    <div className="filter-builder max-w-5xl mx-auto p-4 bg-slate-50 min-h-screen">
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <h1 className="text-xl font-bold text-slate-800">STRIKE SCREENER</h1>
        <div className="text-xs text-slate-500">
          {groups.reduce((acc, g) => acc + g.conditions.length, 0)} conditions
        </div>
      </div>

      {/* Magic Filters */}
      <div className="bg-gradient-to-r from-slate-100 to-slate-50 border border-slate-200 rounded-lg p-3 mb-4">
        <div className="flex items-center gap-2 mb-2">
          <Sparkles className="text-amber-500" size={16} />
          <span className="font-semibold text-slate-700 text-sm">MAGIC FILTERS</span>
          <button className="px-2 py-0.5 bg-white border border-slate-300 rounded text-xs hover:bg-slate-50">Append</button>
          <button className="px-2 py-0.5 bg-white border border-slate-300 rounded text-xs hover:bg-slate-50">Replace</button>
        </div>
        <input
          type="text"
          value={magicFilter}
          onChange={(e) => setMagicFilter(e.target.value)}
          placeholder="Type: 'RSI above 60 and close above EMA 20' or 'MACD crossover'"
          className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-teal-400 focus:border-transparent"
        />
      </div>

      {/* Segment Selector */}
      <div className="flex items-center gap-2 mb-3 text-xs text-slate-600">
        <span>Strike passes <strong className="text-slate-800">all</strong> filters in</span>
        <select
          value={segment}
          onChange={(e) => setSegment(e.target.value)}
          className="font-semibold text-teal-600 border-b border-teal-400 bg-transparent focus:outline-none cursor-pointer"
        >
          {SEGMENTS.map(seg => (
            <option key={seg.value} value={seg.value}>{seg.label}</option>
          ))}
        </select>
        <span>segment:</span>
      </div>

      {/* Filter Groups */}
      {groups.map((group, groupIndex) => (
        <div key={group.id} className="mb-4">
          {groupIndex > 0 && (
            <div className="flex items-center gap-2 my-4">
              <div className="flex-1 h-px bg-slate-300" />
              <span className="px-3 py-1 bg-amber-100 text-amber-700 rounded-full text-xs font-bold border border-amber-200">
                {group.logic}
              </span>
              <div className="flex-1 h-px bg-slate-300" />
            </div>
          )}

          <div className="space-y-2">
            {group.conditions.map(condition => (
              <FilterRow
                key={condition.id}
                condition={condition}
                onUpdate={updateCondition}
                onDelete={deleteCondition}
                onDuplicate={duplicateCondition}
              />
            ))}
          </div>

          <div className="flex gap-2 mt-3">
            <button
              onClick={() => addCondition(group.id)}
              className="flex items-center gap-1 px-3 py-1.5 bg-teal-600 text-white rounded-lg text-xs font-medium hover:bg-teal-700 transition-colors"
            >
              <Plus size={14} />
            </button>
            <button
              onClick={addGroup}
              className="flex items-center gap-1 px-3 py-1.5 bg-teal-50 text-teal-700 border border-teal-200 rounded-lg text-xs font-medium hover:bg-teal-100 transition-colors"
            >
              <Plus size={14} /> OR Group
            </button>
          </div>
        </div>
      ))}

      {/* Action Buttons */}
      <div className="flex flex-wrap gap-2 mt-6 pt-4 border-t border-slate-200">
        <button
          onClick={runScan}
          disabled={isScanning}
          className="flex items-center gap-2 px-5 py-2.5 bg-emerald-600 text-white rounded-lg text-sm font-medium hover:bg-emerald-700 disabled:opacity-50 transition-colors"
        >
          <Play size={16} />
          {isScanning ? 'Scanning...' : 'Run Scan'}
        </button>
        <button className="flex items-center gap-2 px-4 py-2.5 border border-slate-300 rounded-lg text-sm font-medium hover:bg-slate-50 transition-colors">
          <Save size={16} /> Save
        </button>
        <button className="flex items-center gap-2 px-4 py-2.5 border border-amber-300 text-amber-700 rounded-lg text-sm font-medium hover:bg-amber-50 transition-colors">
          <History size={16} /> Backtest
        </button>
        <button className="flex items-center gap-2 px-4 py-2.5 border border-sky-300 text-sky-700 rounded-lg text-sm font-medium hover:bg-sky-50 transition-colors">
          <Bell size={16} /> Alert
        </button>
        <button className="flex items-center gap-2 px-4 py-2.5 border border-slate-300 rounded-lg text-sm font-medium hover:bg-slate-50 transition-colors">
          More <MoreHorizontal size={16} />
        </button>
      </div>

      {/* Results Preview */}
      {results.length > 0 && (
        <div className="mt-6 p-4 bg-white border border-slate-200 rounded-lg">
          <h3 className="font-semibold text-slate-800 mb-3">Results ({results.length} matches)</h3>
          <div className="text-sm text-slate-600">
            {/* Result table would go here */}
            <pre className="text-xs bg-slate-50 p-2 rounded overflow-auto">
              {JSON.stringify(results.slice(0, 5), null, 2)}
            </pre>
          </div>
        </div>
      )}
    </div>
  );
}
