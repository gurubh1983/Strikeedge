// StrikeEdge Filter Builder - Complete with All Operators + Dark Theme
// File: frontend/web/src/app/screener/FilterBuilder.tsx

"use client";

import React, { useState, useRef, useEffect } from 'react';
import { 
  Settings2, 
  Copy, 
  Files, 
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
  Search,
  Calculator,
  TrendingUp,
  Minus
} from 'lucide-react';

// ============================================
// TYPES
// ============================================

interface IndicatorValue {
  type: 'indicator' | 'number' | 'expression';
  indicator?: string;
  params?: Record<string, number>;
  value?: number;
  offset?: number; // [1] = previous candle, [2] = 2 candles ago
  expression?: ExpressionNode; // For complex math expressions
}

interface ExpressionNode {
  type: 'operator' | 'value';
  operator?: '+' | '-' | '*' | '/' | '%';
  left?: IndicatorValue;
  right?: IndicatorValue;
}

interface FilterCondition {
  id: string;
  left: IndicatorValue;
  operator: string;
  right: IndicatorValue;
  // For range operators
  right2?: IndicatorValue; // e.g., "Between X and Y"
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
  { code: 'TYPICAL', name: 'Typical Price', category: 'Price', params: [], format: () => 'Typical' },
  { code: 'WEIGHTED', name: 'Weighted Close', category: 'Price', params: [], format: () => 'Weighted' },
  
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
  { code: 'KAMA', name: 'KAMA', category: 'Moving Averages',
    params: [{ name: 'period', default: 20, min: 1, max: 500 }],
    format: (p) => `KAMA(${p.period})` },
  
  // RSI
  { code: 'RSI', name: 'RSI', category: 'Momentum',
    params: [{ name: 'period', default: 14, min: 2, max: 100 }],
    format: (p) => `RSI(${p.period})` },
  { code: 'RSI_SMA', name: 'RSI SMA', category: 'Momentum',
    params: [
      { name: 'rsi', default: 14, min: 2, max: 100 },
      { name: 'sma', default: 14, min: 1, max: 100 }
    ],
    format: (p) => `RSI(${p.rsi}) SMA(${p.sma})` },
  
  // Stochastic
  { code: 'STOCH_K', name: 'Stoch %K', category: 'Momentum',
    params: [
      { name: 'k', default: 14, min: 1, max: 100 },
      { name: 'smooth', default: 3, min: 1, max: 50 }
    ],
    format: (p) => `%K(${p.k},${p.smooth})` },
  { code: 'STOCH_D', name: 'Stoch %D', category: 'Momentum',
    params: [
      { name: 'k', default: 14, min: 1, max: 100 },
      { name: 'd', default: 3, min: 1, max: 50 }
    ],
    format: (p) => `%D(${p.k},${p.d})` },
  
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
  { code: 'MOMENTUM', name: 'Momentum', category: 'Momentum',
    params: [{ name: 'period', default: 10, min: 1, max: 100 }],
    format: (p) => `Mom(${p.period})` },
  { code: 'TSI', name: 'TSI', category: 'Momentum',
    params: [
      { name: 'fast', default: 13, min: 1, max: 50 },
      { name: 'slow', default: 25, min: 1, max: 100 }
    ],
    format: (p) => `TSI(${p.fast},${p.slow})` },
  
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
  
  // Supertrend & Others
  { code: 'SUPERTREND', name: 'Supertrend', category: 'Trend',
    params: [
      { name: 'period', default: 10, min: 1, max: 100 },
      { name: 'mult', default: 3, min: 1, max: 10 }
    ],
    format: (p) => `ST(${p.period},${p.mult})` },
  { code: 'PSAR', name: 'Parabolic SAR', category: 'Trend',
    params: [
      { name: 'af', default: 0.02, min: 0.01, max: 0.2 },
      { name: 'max', default: 0.2, min: 0.1, max: 0.5 }
    ],
    format: (p) => `PSAR(${p.af},${p.max})` },
  { code: 'AROON_UP', name: 'Aroon Up', category: 'Trend',
    params: [{ name: 'period', default: 25, min: 1, max: 100 }],
    format: (p) => `AroonUp(${p.period})` },
  { code: 'AROON_DOWN', name: 'Aroon Down', category: 'Trend',
    params: [{ name: 'period', default: 25, min: 1, max: 100 }],
    format: (p) => `AroonDn(${p.period})` },
  
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
  { code: 'BB_WIDTH', name: 'BB Width', category: 'Volatility',
    params: [{ name: 'period', default: 20, min: 1, max: 100 }],
    format: (p) => `BBW(${p.period})` },
  { code: 'BB_PERCENT', name: 'BB %B', category: 'Volatility',
    params: [{ name: 'period', default: 20, min: 1, max: 100 }],
    format: (p) => `%B(${p.period})` },
  { code: 'KC_UPPER', name: 'Keltner Upper', category: 'Volatility',
    params: [{ name: 'period', default: 20, min: 1, max: 100 }],
    format: (p) => `KCU(${p.period})` },
  { code: 'KC_LOWER', name: 'Keltner Lower', category: 'Volatility',
    params: [{ name: 'period', default: 20, min: 1, max: 100 }],
    format: (p) => `KCL(${p.period})` },
  { code: 'DC_UPPER', name: 'Donchian Upper', category: 'Volatility',
    params: [{ name: 'period', default: 20, min: 1, max: 100 }],
    format: (p) => `DCU(${p.period})` },
  { code: 'DC_LOWER', name: 'Donchian Lower', category: 'Volatility',
    params: [{ name: 'period', default: 20, min: 1, max: 100 }],
    format: (p) => `DCL(${p.period})` },
  
  // Volume
  { code: 'VOLUME', name: 'Volume', category: 'Volume', params: [], format: () => 'Volume' },
  { code: 'VOLUME_SMA', name: 'Volume SMA', category: 'Volume',
    params: [{ name: 'period', default: 20, min: 1, max: 100 }],
    format: (p) => `VolSMA(${p.period})` },
  { code: 'OBV', name: 'OBV', category: 'Volume', params: [], format: () => 'OBV' },
  { code: 'CMF', name: 'CMF', category: 'Volume',
    params: [{ name: 'period', default: 20, min: 1, max: 100 }],
    format: (p) => `CMF(${p.period})` },
  { code: 'ADL', name: 'A/D Line', category: 'Volume', params: [], format: () => 'ADL' },
  { code: 'VWMA', name: 'VWMA', category: 'Volume',
    params: [{ name: 'period', default: 20, min: 1, max: 100 }],
    format: (p) => `VWMA(${p.period})` },
  
  // Candlestick Patterns
  { code: 'DOJI', name: 'Doji', category: 'Patterns', params: [], format: () => 'Doji' },
  { code: 'HAMMER', name: 'Hammer', category: 'Patterns', params: [], format: () => 'Hammer' },
  { code: 'INV_HAMMER', name: 'Inverted Hammer', category: 'Patterns', params: [], format: () => 'InvHammer' },
  { code: 'ENGULF_BULL', name: 'Bullish Engulfing', category: 'Patterns', params: [], format: () => 'BullEngulf' },
  { code: 'ENGULF_BEAR', name: 'Bearish Engulfing', category: 'Patterns', params: [], format: () => 'BearEngulf' },
  { code: 'MORNING_STAR', name: 'Morning Star', category: 'Patterns', params: [], format: () => 'MornStar' },
  { code: 'EVENING_STAR', name: 'Evening Star', category: 'Patterns', params: [], format: () => 'EveStar' },
  { code: 'THREE_WHITE', name: '3 White Soldiers', category: 'Patterns', params: [], format: () => '3White' },
  { code: 'THREE_BLACK', name: '3 Black Crows', category: 'Patterns', params: [], format: () => '3Black' },
  { code: 'SHOOTING_STAR', name: 'Shooting Star', category: 'Patterns', params: [], format: () => 'ShootStar' },
  { code: 'HARAMI_BULL', name: 'Bullish Harami', category: 'Patterns', params: [], format: () => 'BullHarami' },
  { code: 'HARAMI_BEAR', name: 'Bearish Harami', category: 'Patterns', params: [], format: () => 'BearHarami' },
  { code: 'PIERCING', name: 'Piercing Line', category: 'Patterns', params: [], format: () => 'Piercing' },
  { code: 'DARK_CLOUD', name: 'Dark Cloud Cover', category: 'Patterns', params: [], format: () => 'DarkCloud' },
  
  // Price Action
  { code: 'PDH', name: 'Prev Day High', category: 'Price Action', params: [], format: () => 'PDH' },
  { code: 'PDL', name: 'Prev Day Low', category: 'Price Action', params: [], format: () => 'PDL' },
  { code: 'PDC', name: 'Prev Day Close', category: 'Price Action', params: [], format: () => 'PDC' },
  { code: 'PWH', name: 'Prev Week High', category: 'Price Action', params: [], format: () => 'PWH' },
  { code: 'PWL', name: 'Prev Week Low', category: 'Price Action', params: [], format: () => 'PWL' },
  { code: 'DAY_OPEN', name: 'Day Open', category: 'Price Action', params: [], format: () => 'DayOpen' },
  { code: 'CHANGE_PCT', name: 'Change %', category: 'Price Action', params: [], format: () => 'Chg%' },
  { code: 'GAP_PCT', name: 'Gap %', category: 'Price Action', params: [], format: () => 'Gap%' },
  { code: 'RANGE_PCT', name: 'Range %', category: 'Price Action', params: [], format: () => 'Range%' },
  { code: 'HIGH_N', name: 'Highest', category: 'Price Action',
    params: [{ name: 'n', default: 20, min: 1, max: 252 }],
    format: (p) => `High(${p.n})` },
  { code: 'LOW_N', name: 'Lowest', category: 'Price Action',
    params: [{ name: 'n', default: 20, min: 1, max: 252 }],
    format: (p) => `Low(${p.n})` },
  
  // Pivot Points
  { code: 'PIVOT', name: 'Pivot', category: 'Pivots', params: [], format: () => 'Pivot' },
  { code: 'R1', name: 'R1', category: 'Pivots', params: [], format: () => 'R1' },
  { code: 'R2', name: 'R2', category: 'Pivots', params: [], format: () => 'R2' },
  { code: 'R3', name: 'R3', category: 'Pivots', params: [], format: () => 'R3' },
  { code: 'S1', name: 'S1', category: 'Pivots', params: [], format: () => 'S1' },
  { code: 'S2', name: 'S2', category: 'Pivots', params: [], format: () => 'S2' },
  { code: 'S3', name: 'S3', category: 'Pivots', params: [], format: () => 'S3' },
  { code: 'CPR_TOP', name: 'CPR Top', category: 'Pivots', params: [], format: () => 'CPR Top' },
  { code: 'CPR_BOT', name: 'CPR Bottom', category: 'Pivots', params: [], format: () => 'CPR Bot' },
  
  // Options Greeks
  { code: 'DELTA', name: 'Delta', category: 'Options', params: [], format: () => 'Delta' },
  { code: 'GAMMA', name: 'Gamma', category: 'Options', params: [], format: () => 'Gamma' },
  { code: 'THETA', name: 'Theta', category: 'Options', params: [], format: () => 'Theta' },
  { code: 'VEGA', name: 'Vega', category: 'Options', params: [], format: () => 'Vega' },
  { code: 'IV', name: 'IV', category: 'Options', params: [], format: () => 'IV' },
  { code: 'IV_RANK', name: 'IV Rank', category: 'Options', params: [], format: () => 'IVR' },
  { code: 'IV_PCTL', name: 'IV Percentile', category: 'Options', params: [], format: () => 'IVP' },
  { code: 'OI', name: 'Open Interest', category: 'Options', params: [], format: () => 'OI' },
  { code: 'OI_CHG', name: 'OI Change', category: 'Options', params: [], format: () => 'OI Chg' },
  { code: 'OI_CHG_PCT', name: 'OI Change %', category: 'Options', params: [], format: () => 'OI%' },
  { code: 'PCR', name: 'Put Call Ratio', category: 'Options', params: [], format: () => 'PCR' },
  { code: 'VOL_OI', name: 'Volume/OI', category: 'Options', params: [], format: () => 'V/OI' },
  { code: 'MAX_PAIN', name: 'Max Pain', category: 'Options', params: [], format: () => 'MaxPain' },
  
  // Aggregations
  { code: 'MAX', name: 'Max of', category: 'Aggregations',
    params: [{ name: 'n', default: 10, min: 1, max: 100 }],
    format: (p) => `Max(${p.n})` },
  { code: 'MIN', name: 'Min of', category: 'Aggregations',
    params: [{ name: 'n', default: 10, min: 1, max: 100 }],
    format: (p) => `Min(${p.n})` },
  { code: 'SUM', name: 'Sum of', category: 'Aggregations',
    params: [{ name: 'n', default: 10, min: 1, max: 100 }],
    format: (p) => `Sum(${p.n})` },
  { code: 'AVG', name: 'Average of', category: 'Aggregations',
    params: [{ name: 'n', default: 10, min: 1, max: 100 }],
    format: (p) => `Avg(${p.n})` },
  { code: 'STDEV', name: 'Std Dev', category: 'Aggregations',
    params: [{ name: 'n', default: 20, min: 1, max: 100 }],
    format: (p) => `StDev(${p.n})` },
];

// ============================================
// OPERATORS - Complete Set
// ============================================

const COMPARISON_OPERATORS = [
  { value: 'gt', label: '>', fullLabel: 'Greater Than', category: 'Comparison' },
  { value: 'gte', label: '≥', fullLabel: 'Greater or Equal', category: 'Comparison' },
  { value: 'lt', label: '<', fullLabel: 'Less Than', category: 'Comparison' },
  { value: 'lte', label: '≤', fullLabel: 'Less or Equal', category: 'Comparison' },
  { value: 'eq', label: '=', fullLabel: 'Equals', category: 'Comparison' },
  { value: 'neq', label: '≠', fullLabel: 'Not Equals', category: 'Comparison' },
];

const CROSSOVER_OPERATORS = [
  { value: 'crosses_above', label: '⬆ Cross', fullLabel: 'Crosses Above', category: 'Crossover' },
  { value: 'crosses_below', label: '⬇ Cross', fullLabel: 'Crosses Below', category: 'Crossover' },
  { value: 'crosses', label: '✕ Cross', fullLabel: 'Crosses (Either)', category: 'Crossover' },
];

const RANGE_OPERATORS = [
  { value: 'between', label: 'Between', fullLabel: 'Is Between X and Y', category: 'Range' },
  { value: 'not_between', label: 'Not Btwn', fullLabel: 'Not Between X and Y', category: 'Range' },
  { value: 'within_pct', label: 'Within %', fullLabel: 'Within X% of', category: 'Range' },
];

const CHANGE_OPERATORS = [
  { value: 'rising', label: '↗ Rising', fullLabel: 'Rising for N bars', category: 'Change' },
  { value: 'falling', label: '↘ Falling', fullLabel: 'Falling for N bars', category: 'Change' },
  { value: 'pct_change_gt', label: '%Δ >', fullLabel: '% Change Greater Than', category: 'Change' },
  { value: 'pct_change_lt', label: '%Δ <', fullLabel: '% Change Less Than', category: 'Change' },
  { value: 'point_change_gt', label: 'Δ >', fullLabel: 'Point Change Greater Than', category: 'Change' },
  { value: 'point_change_lt', label: 'Δ <', fullLabel: 'Point Change Less Than', category: 'Change' },
];

const POSITION_OPERATORS = [
  { value: 'highest_in', label: 'Highest', fullLabel: 'Is Highest in N bars', category: 'Position' },
  { value: 'lowest_in', label: 'Lowest', fullLabel: 'Is Lowest in N bars', category: 'Position' },
  { value: 'above_avg', label: '> Avg', fullLabel: 'Above N-bar Average', category: 'Position' },
  { value: 'below_avg', label: '< Avg', fullLabel: 'Below N-bar Average', category: 'Position' },
];

const MATH_OPERATORS = [
  { value: 'add', label: '+', fullLabel: 'Add' },
  { value: 'subtract', label: '−', fullLabel: 'Subtract' },
  { value: 'multiply', label: '×', fullLabel: 'Multiply' },
  { value: 'divide', label: '÷', fullLabel: 'Divide' },
  { value: 'mod', label: '%', fullLabel: 'Modulo' },
];

const ALL_OPERATORS = [
  ...COMPARISON_OPERATORS,
  ...CROSSOVER_OPERATORS,
  ...RANGE_OPERATORS,
  ...CHANGE_OPERATORS,
  ...POSITION_OPERATORS,
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

const OFFSET_OPTIONS = [
  { value: 0, label: 'Current' },
  { value: 1, label: '[1] Prev' },
  { value: 2, label: '[2]' },
  { value: 3, label: '[3]' },
  { value: 5, label: '[5]' },
  { value: 10, label: '[10]' },
];

// ============================================
// INDICATOR SELECTOR COMPONENT (Dark Theme)
// ============================================

interface IndicatorSelectorProps {
  value: IndicatorValue;
  onChange: (value: IndicatorValue) => void;
  showNumber?: boolean;
  showMath?: boolean;
}

function IndicatorSelector({ value, onChange, showNumber = true, showMath = false }: IndicatorSelectorProps) {
  const [showPicker, setShowPicker] = useState(false);
  const [showOffsetPicker, setShowOffsetPicker] = useState(false);
  const [search, setSearch] = useState('');
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (ref.current && !ref.current.contains(e.target as Node)) {
        setShowPicker(false);
        setShowOffsetPicker(false);
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
      params: defaultParams,
      offset: value.offset || 0
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

  const handleOffsetChange = (offset: number) => {
    onChange({ ...value, offset });
    setShowOffsetPicker(false);
  };

  return (
    <div className="relative inline-flex items-center gap-0.5" ref={ref}>
      {value.type === 'indicator' && indicator ? (
        <div className="flex items-center bg-slate-700/50 border border-slate-600 rounded px-1.5 py-0.5">
          <span 
            className="text-slate-200 text-xs font-medium cursor-pointer hover:text-blue-400 px-0.5"
            onClick={() => setShowPicker(true)}
          >
            {indicator.name}
          </span>
          {indicator.params.length > 0 && (
            <>
              <span className="text-slate-500 text-xs">(</span>
              {indicator.params.map((param, idx) => (
                <React.Fragment key={param.name}>
                  <input
                    type="number"
                    value={value.params?.[param.name] || param.default}
                    onChange={(e) => handleParamChange(param.name, parseInt(e.target.value) || param.default)}
                    className="w-8 text-center bg-blue-600 text-white rounded text-xs font-bold mx-0.5 focus:outline-none focus:ring-1 focus:ring-blue-400 [appearance:textfield] [&::-webkit-outer-spin-button]:appearance-none [&::-webkit-inner-spin-button]:appearance-none"
                    min={param.min}
                    max={param.max}
                  />
                  {idx < indicator.params.length - 1 && <span className="text-slate-500 text-xs">,</span>}
                </React.Fragment>
              ))}
              <span className="text-slate-500 text-xs">)</span>
            </>
          )}
          {/* Offset selector */}
          {(value.offset ?? 0) > 0 && (
            <span 
              className="text-amber-400 text-xs font-bold ml-0.5 cursor-pointer hover:text-amber-300"
              onClick={() => setShowOffsetPicker(true)}
            >
              [{value.offset}]
            </span>
          )}
        </div>
      ) : value.type === 'number' ? (
        <input
          type="number"
          value={value.value || 0}
          onChange={(e) => onChange({ type: 'number', value: parseFloat(e.target.value) || 0 })}
          className="w-16 text-center bg-blue-600 text-white rounded text-xs font-bold px-2 py-1 focus:outline-none focus:ring-1 focus:ring-blue-400 [appearance:textfield] [&::-webkit-outer-spin-button]:appearance-none [&::-webkit-inner-spin-button]:appearance-none"
        />
      ) : (
        <button
          onClick={() => setShowPicker(true)}
          className="text-xs text-blue-400 hover:text-blue-300 px-2 py-1 border border-slate-600 rounded hover:bg-slate-700"
        >
          Select...
        </button>
      )}

      {/* Dropdown toggle */}
      <button
        onClick={() => setShowPicker(!showPicker)}
        className="p-0.5 text-slate-500 hover:text-blue-400"
      >
        <ChevronDown size={12} />
      </button>

      {/* Offset button (for lookback) */}
      {value.type === 'indicator' && (
        <button
          onClick={() => setShowOffsetPicker(!showOffsetPicker)}
          className={`p-0.5 text-xs rounded ${(value.offset ?? 0) > 0 ? 'text-amber-400' : 'text-slate-500 hover:text-amber-400'}`}
          title="Candle offset [1]=previous"
        >
          [n]
        </button>
      )}

      {/* Offset Picker */}
      {showOffsetPicker && (
        <div className="absolute top-full left-0 mt-1 w-28 bg-slate-800 border border-slate-600 rounded-lg shadow-xl z-50 py-1">
          <div className="px-2 py-1 text-[10px] text-slate-400 uppercase">Offset</div>
          {OFFSET_OPTIONS.map(opt => (
            <div
              key={opt.value}
              onClick={() => handleOffsetChange(opt.value)}
              className={`px-3 py-1.5 text-xs cursor-pointer hover:bg-slate-700 ${
                value.offset === opt.value ? 'bg-blue-600/30 text-blue-400' : 'text-slate-300'
              }`}
            >
              {opt.label}
            </div>
          ))}
        </div>
      )}

      {/* Main Picker Dropdown */}
      {showPicker && (
        <div className="absolute top-full left-0 mt-1 w-72 bg-slate-800 border border-slate-600 rounded-lg shadow-xl z-50 overflow-hidden">
          {/* Search */}
          <div className="p-2 border-b border-slate-700 bg-slate-800/80">
            <div className="relative">
              <Search size={14} className="absolute left-2 top-1/2 -translate-y-1/2 text-slate-500" />
              <input
                type="text"
                placeholder="Search indicators..."
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                className="w-full pl-7 pr-2 py-1.5 text-xs bg-slate-700 border border-slate-600 rounded text-slate-200 placeholder-slate-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
                autoFocus
              />
            </div>
          </div>

          {/* Number option */}
          {showNumber && (
            <div
              onClick={() => {
                onChange({ type: 'number', value: 0 });
                setShowPicker(false);
              }}
              className="px-3 py-2 text-xs cursor-pointer hover:bg-slate-700 border-b border-slate-700 font-medium text-blue-400 flex items-center gap-2"
            >
              <Calculator size={14} /> Enter Number Value
            </div>
          )}

          {/* Categories */}
          <div className="max-h-72 overflow-y-auto">
            {categories.map(category => {
              const items = filteredIndicators.filter(i => i.category === category);
              if (items.length === 0) return null;
              return (
                <div key={category}>
                  <div className="px-2 py-1.5 bg-slate-900/50 text-[10px] font-semibold text-slate-500 uppercase tracking-wider sticky top-0">
                    {category}
                  </div>
                  {items.map(ind => (
                    <div
                      key={ind.code}
                      onClick={() => handleSelectIndicator(ind)}
                      className={`px-3 py-1.5 text-xs cursor-pointer hover:bg-slate-700 ${
                        value.indicator === ind.code ? 'bg-blue-600/20 text-blue-400' : 'text-slate-300'
                      }`}
                    >
                      {ind.name}
                      {ind.params.length > 0 && (
                        <span className="text-slate-500 ml-1">
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
// OPERATOR SELECTOR (Dark Theme)
// ============================================

interface OperatorSelectorProps {
  value: string;
  onChange: (value: string) => void;
  showRange?: boolean;
}

function OperatorSelector({ value, onChange, showRange = false }: OperatorSelectorProps) {
  const [showDropdown, setShowDropdown] = useState(false);
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (ref.current && !ref.current.contains(e.target as Node)) {
        setShowDropdown(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const selectedOp = ALL_OPERATORS.find(o => o.value === value);
  const operatorCategories = ['Comparison', 'Crossover', 'Range', 'Change', 'Position'];

  return (
    <div className="relative" ref={ref}>
      <button
        onClick={() => setShowDropdown(!showDropdown)}
        className="px-2 py-1 text-xs font-bold text-amber-400 bg-amber-900/30 border border-amber-700/50 rounded hover:bg-amber-900/50 min-w-[36px]"
      >
        {selectedOp?.label || '>'}
      </button>

      {showDropdown && (
        <div className="absolute top-full left-1/2 -translate-x-1/2 mt-1 w-48 bg-slate-800 border border-slate-600 rounded-lg shadow-xl z-50 py-1 max-h-80 overflow-y-auto">
          {operatorCategories.map(category => {
            const ops = ALL_OPERATORS.filter(o => o.category === category);
            if (ops.length === 0) return null;
            return (
              <div key={category}>
                <div className="px-2 py-1 text-[10px] text-slate-500 uppercase font-semibold bg-slate-900/50">
                  {category}
                </div>
                {ops.map(op => (
                  <div
                    key={op.value}
                    onClick={() => {
                      onChange(op.value);
                      setShowDropdown(false);
                    }}
                    className={`px-3 py-1.5 text-xs cursor-pointer hover:bg-slate-700 flex items-center gap-2 ${
                      value === op.value ? 'bg-blue-600/20 text-blue-400' : 'text-slate-300'
                    }`}
                  >
                    <span className="font-bold text-amber-400 w-12">{op.label}</span>
                    <span className="text-slate-400 text-[11px]">{op.fullLabel}</span>
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

// ============================================
// MATH EXPRESSION BUILDER
// ============================================

interface MathExpressionProps {
  baseValue: IndicatorValue;
  onChange: (value: IndicatorValue) => void;
}

function MathExpressionBuilder({ baseValue, onChange }: MathExpressionProps) {
  const [showMathOps, setShowMathOps] = useState(false);
  const [mathOp, setMathOp] = useState<string | null>(null);
  const [mathValue, setMathValue] = useState<IndicatorValue>({ type: 'number', value: 0 });

  const handleAddMath = (op: string) => {
    setMathOp(op);
    setShowMathOps(false);
  };

  const handleApplyMath = () => {
    if (mathOp) {
      onChange({
        type: 'expression',
        expression: {
          type: 'operator',
          operator: mathOp as any,
          left: baseValue,
          right: mathValue
        }
      });
    }
  };

  return (
    <div className="flex items-center gap-1">
      <button
        onClick={() => setShowMathOps(!showMathOps)}
        className="p-1 text-slate-500 hover:text-blue-400 rounded hover:bg-slate-700"
        title="Add math operation"
      >
        <Calculator size={12} />
      </button>

      {showMathOps && (
        <div className="absolute top-full left-0 mt-1 bg-slate-800 border border-slate-600 rounded shadow-lg z-50 p-1 flex gap-1">
          {MATH_OPERATORS.map(op => (
            <button
              key={op.value}
              onClick={() => handleAddMath(op.value)}
              className="w-7 h-7 flex items-center justify-center text-amber-400 hover:bg-slate-700 rounded font-bold"
              title={op.fullLabel}
            >
              {op.label}
            </button>
          ))}
        </div>
      )}

      {mathOp && (
        <>
          <span className="text-amber-400 font-bold text-sm">{MATH_OPERATORS.find(m => m.value === mathOp)?.label}</span>
          <IndicatorSelector
            value={mathValue}
            onChange={setMathValue}
            showNumber={true}
          />
          <button
            onClick={handleApplyMath}
            className="px-2 py-0.5 text-xs bg-green-600 text-white rounded hover:bg-green-500"
          >
            ✓
          </button>
          <button
            onClick={() => setMathOp(null)}
            className="px-2 py-0.5 text-xs bg-red-600 text-white rounded hover:bg-red-500"
          >
            ✕
          </button>
        </>
      )}
    </div>
  );
}

// ============================================
// FILTER ROW COMPONENT (Dark Theme)
// ============================================

interface FilterRowProps {
  condition: FilterCondition;
  onUpdate: (id: string, updates: Partial<FilterCondition>) => void;
  onDelete: (id: string) => void;
  onDuplicate: (id: string) => void;
}

function FilterRow({ condition, onUpdate, onDelete, onDuplicate }: FilterRowProps) {
  const [showTimeframePicker, setShowTimeframePicker] = useState(false);
  const isRangeOperator = ['between', 'not_between'].includes(condition.operator);

  return (
    <div className="filter-row flex items-center gap-1.5 py-2 px-3 bg-slate-800/50 border border-slate-700 rounded-lg hover:border-blue-500/50 hover:bg-slate-800 transition-all group">
      {/* Drag Handle */}
      <div className="cursor-grab text-slate-600 hover:text-slate-400">
        <GripVertical size={14} />
      </div>

      {/* Bullet */}
      <div className="w-2 h-2 rounded-full bg-blue-500" />

      {/* LEFT Indicator */}
      <IndicatorSelector
        value={condition.left}
        onChange={(v) => onUpdate(condition.id, { left: v })}
        showNumber={false}
        showMath={true}
      />

      {/* OPERATOR */}
      <OperatorSelector
        value={condition.operator}
        onChange={(v) => onUpdate(condition.id, { operator: v })}
      />

      {/* RIGHT Indicator/Value */}
      <IndicatorSelector
        value={condition.right}
        onChange={(v) => onUpdate(condition.id, { right: v })}
        showNumber={true}
      />

      {/* Second value for range operators */}
      {isRangeOperator && (
        <>
          <span className="text-slate-500 text-xs">and</span>
          <IndicatorSelector
            value={condition.right2 || { type: 'number', value: 0 }}
            onChange={(v) => onUpdate(condition.id, { right2: v })}
            showNumber={true}
          />
        </>
      )}

      {/* TIMEFRAME */}
      <div className="relative">
        <button
          onClick={() => setShowTimeframePicker(!showTimeframePicker)}
          className="px-2 py-1 text-[10px] font-semibold text-slate-400 bg-slate-700 border border-slate-600 rounded hover:bg-slate-600"
        >
          {TIMEFRAMES.find(t => t.value === condition.timeframe)?.label || 'D'}
        </button>
        {showTimeframePicker && (
          <div className="absolute top-full right-0 mt-1 w-20 bg-slate-800 border border-slate-600 rounded-lg shadow-xl z-50 py-1">
            {TIMEFRAMES.map(tf => (
              <div
                key={tf.value}
                onClick={() => {
                  onUpdate(condition.id, { timeframe: tf.value });
                  setShowTimeframePicker(false);
                }}
                className={`px-3 py-1.5 text-xs cursor-pointer hover:bg-slate-700 text-center ${
                  condition.timeframe === tf.value ? 'bg-blue-600/20 text-blue-400 font-medium' : 'text-slate-400'
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
        <button onClick={() => onDuplicate(condition.id)} className="p-1.5 hover:bg-slate-700 rounded" title="Duplicate">
          <Files size={13} className="text-slate-500 hover:text-blue-400" />
        </button>
        <button onClick={() => navigator.clipboard.writeText(JSON.stringify(condition))} className="p-1.5 hover:bg-slate-700 rounded" title="Copy">
          <Copy size={13} className="text-slate-500 hover:text-blue-400" />
        </button>
        <button onClick={() => onDelete(condition.id)} className="p-1.5 hover:bg-red-900/30 rounded" title="Delete">
          <X size={13} className="text-slate-500 hover:text-red-400" />
        </button>
      </div>
    </div>
  );
}

// ============================================
// MAIN FILTER BUILDER (Dark Theme)
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
          left: { type: 'indicator', indicator: 'RSI', params: { period: 14 }, offset: 0 },
          operator: 'crosses_above',
          right: { type: 'indicator', indicator: 'RSI_SMA', params: { rsi: 14, sma: 14 }, offset: 0 },
          timeframe: '15m',
        },
        {
          id: '1-2',
          left: { type: 'indicator', indicator: 'CLOSE', params: {}, offset: 0 },
          operator: 'gt',
          right: { type: 'indicator', indicator: 'EMA', params: { period: 20 }, offset: 0 },
          timeframe: '15m',
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
              left: { type: 'indicator', indicator: 'RSI', params: { period: 14 }, offset: 0 },
              operator: 'gt',
              right: { type: 'number', value: 60 },
              timeframe: '15m',
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
      const { runTechnicalScan } = await import('../../lib/api/client');
      const filterConfig = {
        groups: groups
          .filter((g) => g.conditions.length > 0)
          .map((g) => ({
            logic: g.logic as 'AND' | 'OR',
            conditions: g.conditions.map((c) => ({ left: c.left, operator: c.operator, right: c.right })),
          })),
        group_logic: 'AND' as const,
      };
      const underlyings = segment === 'nifty_options' ? ['NIFTY'] : segment === 'banknifty_options' ? ['BANKNIFTY'] : segment === 'finnifty_options' ? ['FINNIFTY'] : ['NIFTY', 'BANKNIFTY', 'FINNIFTY'];
      const timeframe = groups[0]?.conditions[0]?.timeframe || '15m';
      const { results: scanResults } = await runTechnicalScan({
        underlyings,
        timeframe,
        rules: [],
        filter_config: filterConfig.groups.length > 0 ? filterConfig : undefined,
        candle_days: 5,
        max_strikes_per_underlying: 30,
      });
      setResults(scanResults || []);
    } catch (error) {
      console.error('Scan failed:', error);
    } finally {
      setIsScanning(false);
    }
  };

  return (
    <div className="filter-builder w-full p-4 bg-slate-900 min-h-screen text-slate-200">
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <h1 className="text-xl font-bold text-white">Strike Screener</h1>
        <div className="text-xs text-slate-500">
          {groups.reduce((acc, g) => acc + g.conditions.length, 0)} conditions
        </div>
      </div>

      {/* Magic Filters */}
      <div className="bg-slate-800/50 border border-slate-700 rounded-lg p-3 mb-4">
        <div className="flex items-center gap-2 mb-2">
          <Sparkles className="text-amber-400" size={16} />
          <span className="font-semibold text-slate-300 text-sm">Magic Filters</span>
          <button className="px-2 py-0.5 bg-slate-700 border border-slate-600 rounded text-xs text-slate-400 hover:bg-slate-600">Append</button>
          <button className="px-2 py-0.5 bg-slate-700 border border-slate-600 rounded text-xs text-slate-400 hover:bg-slate-600">Replace</button>
        </div>
        <input
          type="text"
          value={magicFilter}
          onChange={(e) => setMagicFilter(e.target.value)}
          placeholder="Type: 'RSI crosses above 60' or 'MACD bullish crossover on 15min'"
          className="w-full px-3 py-2 bg-slate-700 border border-slate-600 rounded-lg text-sm text-slate-200 placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
        />
      </div>

      {/* Segment Selector */}
      <div className="flex items-center gap-2 mb-3 text-xs text-slate-400">
        <span>Strike passes <strong className="text-slate-200">all</strong> filters in</span>
        <select
          value={segment}
          onChange={(e) => setSegment(e.target.value)}
          className="font-semibold text-blue-400 bg-transparent border-b border-blue-500 focus:outline-none cursor-pointer"
        >
          {SEGMENTS.map(seg => (
            <option key={seg.value} value={seg.value} className="bg-slate-800 text-slate-200">{seg.label}</option>
          ))}
        </select>
        <span>segment:</span>
      </div>

      {/* Filter Groups */}
      {groups.map((group, groupIndex) => (
        <div key={group.id} className="mb-4">
          {groupIndex > 0 && (
            <div className="flex items-center gap-2 my-4">
              <div className="flex-1 h-px bg-slate-700" />
              <button
                onClick={() => {
                  setGroups(groups.map(g =>
                    g.id === group.id ? { ...g, logic: g.logic === 'AND' ? 'OR' : 'AND' } : g
                  ));
                }}
                className="px-3 py-1 bg-amber-900/30 text-amber-400 rounded-full text-xs font-bold border border-amber-700/50 hover:bg-amber-900/50"
              >
                {group.logic}
              </button>
              <div className="flex-1 h-px bg-slate-700" />
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
              className="flex items-center gap-1 px-3 py-1.5 bg-blue-600 text-white rounded-lg text-xs font-medium hover:bg-blue-500 transition-colors"
            >
              <Plus size={14} />
            </button>
            <button
              onClick={addGroup}
              className="flex items-center gap-1 px-3 py-1.5 bg-slate-700 text-slate-300 border border-slate-600 rounded-lg text-xs font-medium hover:bg-slate-600 transition-colors"
            >
              <Plus size={14} /> OR Group
            </button>
          </div>
        </div>
      ))}

      {/* Action Buttons */}
      <div className="flex flex-wrap gap-2 mt-6 pt-4 border-t border-slate-700">
        <button
          onClick={runScan}
          disabled={isScanning}
          className="flex items-center gap-2 px-5 py-2.5 bg-green-600 text-white rounded-lg text-sm font-medium hover:bg-green-500 disabled:opacity-50 transition-colors"
        >
          <Play size={16} />
          {isScanning ? 'Scanning...' : 'Run Scan'}
        </button>
        <button className="flex items-center gap-2 px-4 py-2.5 bg-slate-700 border border-slate-600 text-slate-300 rounded-lg text-sm font-medium hover:bg-slate-600 transition-colors">
          <Save size={16} /> Save
        </button>
        <button className="flex items-center gap-2 px-4 py-2.5 bg-slate-700 border border-amber-700/50 text-amber-400 rounded-lg text-sm font-medium hover:bg-amber-900/30 transition-colors">
          <History size={16} /> Backtest
        </button>
        <button className="flex items-center gap-2 px-4 py-2.5 bg-slate-700 border border-blue-700/50 text-blue-400 rounded-lg text-sm font-medium hover:bg-blue-900/30 transition-colors">
          <Bell size={16} /> Alert
        </button>
        <button className="flex items-center gap-2 px-4 py-2.5 bg-slate-700 border border-slate-600 text-slate-400 rounded-lg text-sm font-medium hover:bg-slate-600 transition-colors">
          More <MoreHorizontal size={16} />
        </button>
      </div>

      {/* Results Preview */}
      {results.length > 0 && (
        <div className="mt-6 p-4 bg-slate-800 border border-slate-700 rounded-lg">
          <h3 className="font-semibold text-white mb-3">Results ({results.length} matches)</h3>
          <div className="text-sm">
            <pre className="text-xs bg-slate-900 p-3 rounded overflow-auto text-slate-400 max-h-60">
              {JSON.stringify(results.slice(0, 5), null, 2)}
            </pre>
          </div>
        </div>
      )}
    </div>
  );
}
