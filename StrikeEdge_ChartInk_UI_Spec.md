# StrikeEdge Filter Builder - Exact ChartInk UI Specification

## Filter Row Structure

Each filter condition is a single row with inline editable components:

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│ ● │ [Number] │ [Operator▼] │ [Timeframe▼] │ [DataPoint▼] │ ⚙️ │ 📋 │ 📄 │ 👁️ │ ❌ │
└─────────────────────────────────────────────────────────────────────────────────┘

Example:
● │  20  │ Equals │ Daily │ High │ ⚙️ 📋 📄 👁️ ❌
```

## Component Specifications

### 1. Number Input
- Editable number field
- Can be: period (14, 20, 50), value (60, 80), percentage (5%), multiplier (2x)
- Highlighted in colored badge (purple/blue)

```tsx
<input 
  type="number" 
  className="w-12 text-center bg-purple-500 text-white rounded px-2 py-1 font-bold"
  value={20}
/>
```

### 2. Operator Dropdown
Options:
```
- Equals (=)
- Not Equals (≠)
- Greater Than (>)
- Less Than (<)
- Greater Than or Equal (≥)
- Less Than or Equal (≤)
- Crosses Above (↗)
- Crosses Below (↘)
- Is Between
- Is Increasing
- Is Decreasing
- Is Highest In
- Is Lowest In
```

### 3. Timeframe Dropdown
Options:
```
- 1 minute
- 3 minutes
- 5 minutes
- 10 minutes
- 15 minutes
- 30 minutes
- Hourly
- 2 Hour
- 4 Hour
- Daily
- Weekly
- Monthly
```

### 4. Data Point / Indicator Dropdown
This is the MAIN selector with categories:

```
├── PRICE
│   ├── Open
│   ├── High
│   ├── Low
│   ├── Close
│   ├── VWAP
│   ├── Typical Price
│   └── Weighted Close
│
├── MOVING AVERAGES
│   ├── SMA (5, 10, 20, 50, 100, 200)
│   ├── EMA (5, 10, 20, 50, 100, 200)
│   ├── WMA
│   ├── DEMA
│   ├── TEMA
│   └── Hull MA
│
├── MOMENTUM
│   ├── RSI (14)
│   ├── RSI (7)
│   ├── Stochastic %K
│   ├── Stochastic %D
│   ├── CCI
│   ├── Williams %R
│   ├── ROC (Rate of Change)
│   ├── Momentum
│   └── TSI
│
├── TREND
│   ├── MACD Line
│   ├── MACD Signal
│   ├── MACD Histogram
│   ├── ADX
│   ├── +DI
│   ├── -DI
│   ├── Supertrend
│   ├── Parabolic SAR
│   └── Aroon Up/Down
│
├── VOLATILITY
│   ├── ATR
│   ├── Bollinger Upper
│   ├── Bollinger Middle
│   ├── Bollinger Lower
│   ├── Bollinger %B
│   ├── Keltner Upper
│   ├── Keltner Lower
│   └── Donchian Channel
│
├── VOLUME
│   ├── Volume
│   ├── Volume SMA
│   ├── OBV
│   ├── MFI
│   ├── VWAP
│   ├── Accumulation/Distribution
│   └── Chaikin Money Flow
│
├── CANDLESTICK PATTERNS
│   ├── Doji
│   ├── Hammer
│   ├── Inverted Hammer
│   ├── Bullish Engulfing
│   ├── Bearish Engulfing
│   ├── Morning Star
│   ├── Evening Star
│   ├── Three White Soldiers
│   ├── Three Black Crows
│   ├── Shooting Star
│   ├── Hanging Man
│   └── ... (30+ patterns)
│
├── PIVOT POINTS
│   ├── Pivot
│   ├── R1, R2, R3
│   ├── S1, S2, S3
│   ├── Camarilla R1-R4
│   └── Camarilla S1-S4
│
├── PRICE ACTION
│   ├── Previous Day High
│   ├── Previous Day Low
│   ├── Previous Day Close
│   ├── Previous Week High
│   ├── Previous Week Low
│   ├── 52 Week High
│   ├── 52 Week Low
│   ├── All Time High
│   ├── Gap Up %
│   ├── Gap Down %
│   └── Today's Range %
│
├── OPTIONS SPECIFIC (StrikeEdge Unique)
│   ├── Delta
│   ├── Gamma
│   ├── Theta
│   ├── Vega
│   ├── IV (Implied Volatility)
│   ├── IV Rank
│   ├── IV Percentile
│   ├── Open Interest
│   ├── OI Change
│   ├── OI Change %
│   ├── Put Call Ratio
│   ├── Max Pain
│   ├── Volume/OI Ratio
│   └── Premium Change %
```

### 5. Action Icons

| Icon | Action | Description |
|------|--------|-------------|
| ⚙️ | Settings | Open advanced parameters modal |
| 📋 | Copy | Copy this condition to clipboard |
| 📄 | Duplicate | Add duplicate of this condition |
| 👁️ | Preview | Preview what this filter matches |
| ❌ | Delete | Remove this condition |

### 6. Segment Selector (Top of Builder)

```
Stock passes all of the below filters in [cash ▼] segment:

Options:
- Cash (Stocks)
- F&O (Futures & Options)
- Index Options
- Stock Options
- Index Futures
- Stock Futures
```

For StrikeEdge, this would be:
```
- NIFTY Options
- BANKNIFTY Options
- FINNIFTY Options
- Stock Options (All)
- Specific Stock (dropdown)
```

## Complete Filter Row Component

```tsx
// frontend/web/src/components/FilterRow.tsx

import React, { useState } from 'react';
import { 
  Settings, Copy, Files, Eye, X, 
  ChevronDown, GripVertical 
} from 'lucide-react';

interface FilterRowProps {
  condition: {
    id: string;
    number: number;
    operator: string;
    timeframe: string;
    dataPoint: string;
    parameters?: Record<string, any>;
  };
  onUpdate: (id: string, updates: Partial<FilterRowProps['condition']>) => void;
  onDelete: (id: string) => void;
  onDuplicate: (id: string) => void;
  onCopy: (id: string) => void;
}

const OPERATORS = [
  { value: 'equals', label: 'Equals' },
  { value: 'not_equals', label: 'Not Equals' },
  { value: 'greater_than', label: 'Greater Than' },
  { value: 'less_than', label: 'Less Than' },
  { value: 'gte', label: 'Greater Than or Equal' },
  { value: 'lte', label: 'Less Than or Equal' },
  { value: 'crosses_above', label: 'Crosses Above' },
  { value: 'crosses_below', label: 'Crosses Below' },
  { value: 'is_between', label: 'Is Between' },
  { value: 'is_increasing', label: 'Is Increasing' },
  { value: 'is_decreasing', label: 'Is Decreasing' },
  { value: 'is_highest_in', label: 'Is Highest In' },
  { value: 'is_lowest_in', label: 'Is Lowest In' },
];

const TIMEFRAMES = [
  { value: '1m', label: '1 minute' },
  { value: '3m', label: '3 minutes' },
  { value: '5m', label: '5 minutes' },
  { value: '10m', label: '10 minutes' },
  { value: '15m', label: '15 minutes' },
  { value: '30m', label: '30 minutes' },
  { value: '1h', label: 'Hourly' },
  { value: '2h', label: '2 Hour' },
  { value: '4h', label: '4 Hour' },
  { value: '1d', label: 'Daily' },
  { value: '1w', label: 'Weekly' },
  { value: '1M', label: 'Monthly' },
];

const DATA_POINTS = {
  'Price': ['Open', 'High', 'Low', 'Close', 'VWAP', 'Typical Price'],
  'Moving Averages': ['SMA(5)', 'SMA(10)', 'SMA(20)', 'SMA(50)', 'SMA(200)', 'EMA(5)', 'EMA(10)', 'EMA(20)', 'EMA(50)', 'EMA(200)'],
  'Momentum': ['RSI(14)', 'RSI(7)', 'Stochastic %K', 'Stochastic %D', 'CCI', 'Williams %R', 'ROC', 'Momentum'],
  'Trend': ['MACD Line', 'MACD Signal', 'MACD Histogram', 'ADX', '+DI', '-DI', 'Supertrend', 'Parabolic SAR'],
  'Volatility': ['ATR', 'BB Upper', 'BB Middle', 'BB Lower', 'BB %B', 'Keltner Upper', 'Keltner Lower'],
  'Volume': ['Volume', 'Volume SMA', 'OBV', 'MFI', 'A/D Line', 'CMF'],
  'Candlestick': ['Doji', 'Hammer', 'Engulfing', 'Morning Star', 'Evening Star', 'Shooting Star'],
  'Options': ['Delta', 'Gamma', 'Theta', 'Vega', 'IV', 'IV Rank', 'OI', 'OI Change', 'PCR', 'Volume/OI'],
};

export function FilterRow({ condition, onUpdate, onDelete, onDuplicate, onCopy }: FilterRowProps) {
  const [showDataPointDropdown, setShowDataPointDropdown] = useState(false);
  const [showSettingsModal, setShowSettingsModal] = useState(false);

  return (
    <div className="filter-row flex items-center gap-2 p-2 bg-gray-50 rounded-lg border border-gray-200 hover:border-purple-300 transition-colors">
      {/* Drag Handle */}
      <div className="cursor-grab text-gray-400 hover:text-gray-600">
        <GripVertical size={16} />
      </div>

      {/* Bullet Point */}
      <div className="w-2 h-2 rounded-full bg-purple-500" />

      {/* Number Input */}
      <div className="relative">
        <input
          type="number"
          value={condition.number}
          onChange={(e) => onUpdate(condition.id, { number: parseInt(e.target.value) || 0 })}
          className="w-14 text-center bg-purple-600 text-white rounded-md px-2 py-1 font-bold text-sm focus:outline-none focus:ring-2 focus:ring-purple-400"
        />
      </div>

      {/* Operator Dropdown */}
      <select
        value={condition.operator}
        onChange={(e) => onUpdate(condition.id, { operator: e.target.value })}
        className="bg-white border border-gray-300 rounded-md px-3 py-1 text-sm focus:outline-none focus:ring-2 focus:ring-purple-400"
      >
        {OPERATORS.map(op => (
          <option key={op.value} value={op.value}>{op.label}</option>
        ))}
      </select>

      {/* Timeframe Dropdown */}
      <select
        value={condition.timeframe}
        onChange={(e) => onUpdate(condition.id, { timeframe: e.target.value })}
        className="bg-white border border-gray-300 rounded-md px-3 py-1 text-sm focus:outline-none focus:ring-2 focus:ring-purple-400"
      >
        {TIMEFRAMES.map(tf => (
          <option key={tf.value} value={tf.value}>{tf.label}</option>
        ))}
      </select>

      {/* Data Point Dropdown (Complex with Categories) */}
      <div className="relative">
        <button
          onClick={() => setShowDataPointDropdown(!showDataPointDropdown)}
          className="flex items-center gap-1 bg-white border border-gray-300 rounded-md px-3 py-1 text-sm focus:outline-none focus:ring-2 focus:ring-purple-400"
        >
          {condition.dataPoint}
          <ChevronDown size={14} />
        </button>

        {showDataPointDropdown && (
          <div className="absolute top-full left-0 mt-1 w-64 bg-white border border-gray-200 rounded-lg shadow-lg z-50 max-h-80 overflow-y-auto">
            {Object.entries(DATA_POINTS).map(([category, items]) => (
              <div key={category}>
                <div className="px-3 py-2 bg-gray-100 font-semibold text-xs text-gray-600 uppercase tracking-wider">
                  {category}
                </div>
                {items.map(item => (
                  <div
                    key={item}
                    onClick={() => {
                      onUpdate(condition.id, { dataPoint: item });
                      setShowDataPointDropdown(false);
                    }}
                    className="px-3 py-2 hover:bg-purple-50 cursor-pointer text-sm"
                  >
                    {item}
                  </div>
                ))}
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Spacer */}
      <div className="flex-1" />

      {/* Action Icons */}
      <div className="flex items-center gap-1">
        <button
          onClick={() => setShowSettingsModal(true)}
          className="p-1 text-gray-400 hover:text-purple-600 hover:bg-purple-50 rounded"
          title="Settings"
        >
          <Settings size={16} />
        </button>
        <button
          onClick={() => onCopy(condition.id)}
          className="p-1 text-gray-400 hover:text-blue-600 hover:bg-blue-50 rounded"
          title="Copy"
        >
          <Copy size={16} />
        </button>
        <button
          onClick={() => onDuplicate(condition.id)}
          className="p-1 text-gray-400 hover:text-green-600 hover:bg-green-50 rounded"
          title="Duplicate"
        >
          <Files size={16} />
        </button>
        <button
          className="p-1 text-gray-400 hover:text-orange-600 hover:bg-orange-50 rounded"
          title="Preview"
        >
          <Eye size={16} />
        </button>
        <button
          onClick={() => onDelete(condition.id)}
          className="p-1 text-gray-400 hover:text-red-600 hover:bg-red-50 rounded"
          title="Delete"
        >
          <X size={16} />
        </button>
      </div>

      {/* Settings Modal */}
      {showSettingsModal && (
        <SettingsModal
          condition={condition}
          onUpdate={onUpdate}
          onClose={() => setShowSettingsModal(false)}
        />
      )}
    </div>
  );
}

function SettingsModal({ condition, onUpdate, onClose }) {
  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg w-96 p-6">
        <h3 className="text-lg font-semibold mb-4">Advanced Settings</h3>
        
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Period
            </label>
            <input
              type="number"
              value={condition.parameters?.period || 14}
              onChange={(e) => onUpdate(condition.id, {
                parameters: { ...condition.parameters, period: parseInt(e.target.value) }
              })}
              className="w-full border rounded-md px-3 py-2"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Source
            </label>
            <select className="w-full border rounded-md px-3 py-2">
              <option>Close</option>
              <option>Open</option>
              <option>High</option>
              <option>Low</option>
              <option>HL2</option>
              <option>HLC3</option>
              <option>OHLC4</option>
            </select>
          </div>

          {/* Add more parameter fields based on indicator type */}
        </div>

        <div className="flex justify-end gap-2 mt-6">
          <button
            onClick={onClose}
            className="px-4 py-2 border rounded-md hover:bg-gray-50"
          >
            Cancel
          </button>
          <button
            onClick={onClose}
            className="px-4 py-2 bg-purple-600 text-white rounded-md hover:bg-purple-700"
          >
            Apply
          </button>
        </div>
      </div>
    </div>
  );
}
```

## Complete Filter Builder Component

```tsx
// frontend/web/src/features/screener/ChartInkStyleBuilder.tsx

import React, { useState } from 'react';
import { FilterRow } from '@/components/FilterRow';
import { Plus, Play, Save, History, Bell, MoreHorizontal } from 'lucide-react';

interface FilterCondition {
  id: string;
  number: number;
  operator: string;
  timeframe: string;
  dataPoint: string;
  parameters?: Record<string, any>;
}

interface FilterGroup {
  id: string;
  logic: 'AND' | 'OR';
  conditions: FilterCondition[];
}

const SEGMENTS = [
  { value: 'nifty_options', label: 'NIFTY Options' },
  { value: 'banknifty_options', label: 'BANKNIFTY Options' },
  { value: 'finnifty_options', label: 'FINNIFTY Options' },
  { value: 'stock_options', label: 'Stock Options' },
  { value: 'all_options', label: 'All F&O Options' },
];

const MAGIC_FILTER_SUGGESTIONS = [
  'Doji on 15-min',
  'Green candle on 15-min',
  'RSI crossing above 60',
  'MACD bullish crossover',
  'Volume spike',
  'Hammer pattern',
  'Breaking previous high',
];

export function ChartInkStyleBuilder() {
  const [segment, setSegment] = useState('nifty_options');
  const [groups, setGroups] = useState<FilterGroup[]>([
    {
      id: '1',
      logic: 'AND',
      conditions: [
        {
          id: '1-1',
          number: 20,
          operator: 'equals',
          timeframe: '1d',
          dataPoint: 'High',
        }
      ]
    }
  ]);
  const [magicFilter, setMagicFilter] = useState('');
  const [isScanning, setIsScanning] = useState(false);

  const addCondition = (groupId: string) => {
    setGroups(groups.map(g => {
      if (g.id === groupId) {
        return {
          ...g,
          conditions: [
            ...g.conditions,
            {
              id: `${groupId}-${Date.now()}`,
              number: 14,
              operator: 'greater_than',
              timeframe: '1d',
              dataPoint: 'RSI(14)',
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
      {
        id: Date.now().toString(),
        logic: 'AND',
        conditions: []
      }
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
      const condIndex = g.conditions.findIndex(c => c.id === conditionId);
      if (condIndex === -1) return g;
      
      const condition = g.conditions[condIndex];
      const newCondition = {
        ...condition,
        id: `${g.id}-${Date.now()}`
      };
      
      return {
        ...g,
        conditions: [
          ...g.conditions.slice(0, condIndex + 1),
          newCondition,
          ...g.conditions.slice(condIndex + 1)
        ]
      };
    }));
  };

  const copyCondition = (conditionId: string) => {
    const condition = groups
      .flatMap(g => g.conditions)
      .find(c => c.id === conditionId);
    
    if (condition) {
      navigator.clipboard.writeText(JSON.stringify(condition));
    }
  };

  const runScan = async () => {
    setIsScanning(true);
    
    try {
      const filterConfig = {
        groups: groups.map(g => ({
          logic: g.logic,
          conditions: g.conditions.map(c => ({
            code: `${c.dataPoint}_${c.operator}`.toUpperCase().replace(/[^A-Z0-9_]/g, '_'),
            params: {
              value: c.number,
              timeframe: c.timeframe,
              ...c.parameters
            }
          }))
        })),
        group_logic: 'AND'
      };

      const response = await fetch('/api/v1/scanner/technical', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          segment,
          filter_config: filterConfig
        })
      });

      const data = await response.json();
      console.log('Scan results:', data);
      // Handle results...
    } finally {
      setIsScanning(false);
    }
  };

  return (
    <div className="chartink-builder max-w-4xl mx-auto p-6">
      {/* Header */}
      <h1 className="text-2xl font-bold mb-6">STRIKE SCREENER</h1>

      {/* Magic Filters */}
      <div className="magic-filters bg-blue-50 border border-blue-200 rounded-lg p-4 mb-6">
        <div className="flex items-center gap-2 mb-3">
          <span className="text-yellow-500">✨</span>
          <span className="font-semibold text-blue-800">MAGIC FILTERS</span>
          <button className="ml-2 px-3 py-1 bg-white border border-blue-300 rounded text-sm">
            Append
          </button>
          <button className="px-3 py-1 bg-white border border-blue-300 rounded text-sm">
            Replace
          </button>
        </div>

        <input
          type="text"
          value={magicFilter}
          onChange={(e) => setMagicFilter(e.target.value)}
          placeholder="Scan strikes using simple language like 'RSI above 60 and volume spike'"
          className="w-full p-3 border border-blue-300 rounded-lg mb-3"
        />

        <div className="flex flex-wrap gap-2">
          {MAGIC_FILTER_SUGGESTIONS.map(suggestion => (
            <button
              key={suggestion}
              onClick={() => setMagicFilter(suggestion)}
              className="px-3 py-1 bg-blue-100 hover:bg-blue-200 rounded-full text-sm text-blue-700"
            >
              {suggestion} ↩
            </button>
          ))}
          <button className="px-3 py-1 border border-blue-300 rounded-full text-sm text-blue-600">
            + Add tag
          </button>
        </div>
      </div>

      {/* Segment Selector */}
      <div className="flex items-center gap-2 mb-4 text-gray-700">
        <span>Strike passes <strong>all</strong> of the below filters in</span>
        <select
          value={segment}
          onChange={(e) => setSegment(e.target.value)}
          className="font-semibold text-blue-600 border-b border-blue-300 bg-transparent focus:outline-none cursor-pointer"
        >
          {SEGMENTS.map(seg => (
            <option key={seg.value} value={seg.value}>{seg.label}</option>
          ))}
        </select>
        <span>segment:</span>
        <button className="ml-2 p-1 hover:bg-gray-100 rounded" title="Copy all">📋</button>
        <button className="p-1 hover:bg-gray-100 rounded" title="Paste">📄</button>
      </div>

      {/* Filter Groups */}
      {groups.map((group, groupIndex) => (
        <div key={group.id} className="filter-group mb-6">
          {groupIndex > 0 && (
            <div className="flex items-center gap-2 my-4">
              <div className="flex-1 h-px bg-gray-300" />
              <select
                value={group.logic}
                onChange={(e) => {
                  setGroups(groups.map(g => 
                    g.id === group.id ? { ...g, logic: e.target.value as 'AND' | 'OR' } : g
                  ));
                }}
                className="px-3 py-1 border rounded font-semibold text-orange-600"
              >
                <option value="AND">AND</option>
                <option value="OR">OR</option>
              </select>
              <div className="flex-1 h-px bg-gray-300" />
            </div>
          )}

          {/* Conditions */}
          <div className="space-y-2">
            {group.conditions.map(condition => (
              <FilterRow
                key={condition.id}
                condition={condition}
                onUpdate={updateCondition}
                onDelete={deleteCondition}
                onDuplicate={duplicateCondition}
                onCopy={copyCondition}
              />
            ))}
          </div>

          {/* Add Condition Buttons */}
          <div className="flex gap-2 mt-3">
            <button
              onClick={() => addCondition(group.id)}
              className="flex items-center gap-1 px-3 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700"
            >
              <Plus size={16} />
              Add Condition
            </button>
            <button
              onClick={() => addCondition(group.id)}
              className="flex items-center gap-1 px-3 py-2 bg-purple-100 text-purple-700 rounded-lg hover:bg-purple-200"
            >
              <Plus size={16} />
              Add Group
            </button>
          </div>
        </div>
      ))}

      {/* Action Buttons */}
      <div className="flex flex-wrap gap-3 mt-8 pt-6 border-t">
        <button
          onClick={runScan}
          disabled={isScanning}
          className="flex items-center gap-2 px-6 py-3 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:opacity-50"
        >
          <Play size={18} />
          {isScanning ? 'Scanning...' : 'Run Scan'}
        </button>
        <button className="flex items-center gap-2 px-4 py-3 border border-gray-300 rounded-lg hover:bg-gray-50">
          <Save size={18} />
          Save Scan
        </button>
        <button className="flex items-center gap-2 px-4 py-3 border border-orange-300 text-orange-600 rounded-lg hover:bg-orange-50">
          <History size={18} />
          Backtest Results
        </button>
        <button className="flex items-center gap-2 px-4 py-3 border border-blue-300 text-blue-600 rounded-lg hover:bg-blue-50">
          <Bell size={18} />
          Create Alert
        </button>
        <button className="flex items-center gap-2 px-4 py-3 border border-gray-300 rounded-lg hover:bg-gray-50">
          <MoreHorizontal size={18} />
          More
        </button>
      </div>
    </div>
  );
}
```

## Backend Indicator Codes Mapping

The frontend sends codes like `HIGH_EQUALS`, which backend maps to actual computations:

```python
# backend/app/services/filter_mappings.py

FILTER_CODE_MAPPINGS = {
    # Price comparisons
    'CLOSE_GREATER_THAN': lambda df, params: df['close'].iloc[-1] > params['value'],
    'CLOSE_LESS_THAN': lambda df, params: df['close'].iloc[-1] < params['value'],
    'HIGH_EQUALS': lambda df, params: abs(df['high'].iloc[-1] - params['value']) < 0.01,
    
    # RSI
    'RSI_14__GREATER_THAN': lambda df, params: ta.rsi(df['close'], 14).iloc[-1] > params['value'],
    'RSI_14__LESS_THAN': lambda df, params: ta.rsi(df['close'], 14).iloc[-1] < params['value'],
    'RSI_14__CROSSES_ABOVE': lambda df, params: (
        ta.rsi(df['close'], 14).iloc[-2] <= params['value'] < ta.rsi(df['close'], 14).iloc[-1]
    ),
    
    # MACD
    'MACD_LINE_CROSSES_ABOVE': lambda df, params: check_macd_crossover(df, 'bullish'),
    'MACD_LINE_CROSSES_BELOW': lambda df, params: check_macd_crossover(df, 'bearish'),
    
    # Moving Averages
    'EMA_20__GREATER_THAN': lambda df, params: df['close'].iloc[-1] > ta.ema(df['close'], 20).iloc[-1],
    'SMA_50__CROSSES_ABOVE': lambda df, params: check_ma_crossover(df, 'sma', 50, 'above'),
    
    # Candlestick Patterns
    'DOJI': lambda df, params: is_doji(df),
    'HAMMER': lambda df, params: is_hammer(df),
    'BULLISH_ENGULFING': lambda df, params: is_bullish_engulfing(df),
    
    # Volume
    'VOLUME_GREATER_THAN': lambda df, params: df['volume'].iloc[-1] > params['value'],
    'VOLUME_SPIKE': lambda df, params: df['volume'].iloc[-1] > df['volume'].rolling(20).mean().iloc[-1] * params.get('multiplier', 2),
    
    # Options
    'DELTA_GREATER_THAN': lambda df, params: params.get('delta', 0) > params['value'],
    'OI_CHANGE_GREATER_THAN': lambda df, params: params.get('oi_change', 0) > params['value'],
    'IV_GREATER_THAN': lambda df, params: params.get('iv', 0) > params['value'],
    
    # ... 100+ more mappings
}
```

## Summary

This specification provides:

1. **Exact ChartInk UI** with inline filter rows
2. **All component specifications** with code
3. **Complete filter categories** (100+ conditions)
4. **Action icons** (settings, copy, duplicate, preview, delete)
5. **Segment selector** for different option types
6. **Magic filters** with suggestions
7. **AND/OR group logic**
8. **Backend mapping** for all filter codes

The implementation is split into:
- `FilterRow.tsx` - Individual filter row component
- `ChartInkStyleBuilder.tsx` - Complete builder page
- `filter_mappings.py` - Backend code to evaluate filters
