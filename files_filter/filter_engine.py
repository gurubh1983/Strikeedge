# StrikeEdge Filter Engine - Technical Indicator Calculator
# Synced with frontend ScreenerBuilder (additionalfeatures)

"""
Filter engine that evaluates technical conditions on OHLCV data.
Supports 70+ indicators with customizable parameters.
Frontend indicator codes and param names are aliased to backend internally.
"""

import pandas as pd
import numpy as np
from typing import Any, Callable
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)

# Try to import pandas_ta, fall back to manual calculations if not available
try:
    import pandas_ta as ta
    HAS_PANDAS_TA = True
except ImportError:
    HAS_PANDAS_TA = False
    logger.warning("pandas_ta not installed. Using manual indicator calculations.")


@dataclass
class IndicatorResult:
    """Result of an indicator calculation."""
    value: float
    series: pd.Series | None = None


class FilterEngine:
    """
    Evaluates filter conditions on OHLCV data.
    
    Usage:
        engine = FilterEngine()
        df = pd.DataFrame({...})  # OHLCV data
        
        # Evaluate single indicator
        rsi_value = engine.calculate('RSI', df, {'period': 14})
        
        # Evaluate condition
        result = engine.evaluate_condition(df, {
            'left': {'type': 'indicator', 'indicator': 'RSI', 'params': {'period': 14}},
            'operator': 'gt',
            'right': {'type': 'number', 'value': 60}
        })
    """
    
    # Frontend -> Backend indicator code aliases (ScreenerBuilder sync)
    INDICATOR_ALIASES = {
        'TYPICAL_PRICE': 'TYPICAL_PRICE',  # keep
        'INV_HAMMER': 'INVERTED_HAMMER',
        'ENGULF_BULL': 'BULLISH_ENGULFING',
        'ENGULF_BEAR': 'BEARISH_ENGULFING',
        'THREE_WHITE': 'THREE_WHITE_SOLDIERS',
        'THREE_BLACK': 'THREE_BLACK_CROWS',
        'PDH': 'PREV_DAY_HIGH',
        'PDL': 'PREV_DAY_LOW',
        'PDC': 'PREV_DAY_CLOSE',
        'HIGH_N': 'HIGH_OF_N',
        'LOW_N': 'LOW_OF_N',
        'BB_PERCENT': 'BB_PERCENT_B',
        'VOL_OI': 'VOLUME_OI_RATIO',
        'OI_CHG': 'OI_CHANGE',
        'OI_CHG_PCT': 'OI_CHANGE_PCT',
    }

    # Frontend param name -> Backend param name (per indicator)
    PARAM_ALIASES = {
        'RSI_SMA': {'rsi': 'rsi_period', 'sma': 'sma_period'},
        'STOCH_K': {'k': 'k_period'},
        'STOCH_D': {'k': 'k_period', 'd': 'd_period'},
        'SUPERTREND': {'mult': 'multiplier'},
        'HIGH_OF_N': {'n': 'period'},
        'LOW_OF_N': {'n': 'period'},
    }

    def __init__(self):
        self.indicators = self._register_indicators()
        self.operators = self._register_operators()
    
    # ============================================
    # INDICATOR REGISTRATION
    # ============================================
    
    def _register_indicators(self) -> dict[str, Callable]:
        """Register all available indicators."""
        return {
            # Price
            'OPEN': self._price_open,
            'HIGH': self._price_high,
            'LOW': self._price_low,
            'CLOSE': self._price_close,
            'VWAP': self._vwap,
            'TYPICAL_PRICE': self._typical_price,
            
            # Moving Averages
            'SMA': self._sma,
            'EMA': self._ema,
            'WMA': self._wma,
            'DEMA': self._dema,
            'TEMA': self._tema,
            'HMA': self._hma,
            
            # RSI Family
            'RSI': self._rsi,
            'RSI_SMA': self._rsi_sma,
            
            # Stochastic
            'STOCH_K': self._stochastic_k,
            'STOCH_D': self._stochastic_d,
            
            # Other Momentum
            'CCI': self._cci,
            'WILLR': self._williams_r,
            'MFI': self._mfi,
            'ROC': self._roc,
            'MOMENTUM': self._momentum,
            
            # MACD
            'MACD': self._macd_line,
            'MACD_SIGNAL': self._macd_signal,
            'MACD_HIST': self._macd_histogram,
            
            # ADX Family
            'ADX': self._adx,
            'PLUS_DI': self._plus_di,
            'MINUS_DI': self._minus_di,
            
            # Trend
            'SUPERTREND': self._supertrend,
            'SUPERTREND_DIRECTION': self._supertrend_direction,
            
            # Volatility
            'ATR': self._atr,
            'BB_UPPER': self._bb_upper,
            'BB_MIDDLE': self._bb_middle,
            'BB_LOWER': self._bb_lower,
            'BB_PERCENT_B': self._bb_percent_b,
            'BB_WIDTH': self._bb_width,
            
            # Volume
            'VOLUME': self._volume,
            'VOLUME_SMA': self._volume_sma,
            'OBV': self._obv,
            
            # Candlestick Patterns (return 1 if pattern found, 0 otherwise)
            'DOJI': self._pattern_doji,
            'HAMMER': self._pattern_hammer,
            'INVERTED_HAMMER': self._pattern_inverted_hammer,
            'BULLISH_ENGULFING': self._pattern_bullish_engulfing,
            'BEARISH_ENGULFING': self._pattern_bearish_engulfing,
            'MORNING_STAR': self._pattern_morning_star,
            'EVENING_STAR': self._pattern_evening_star,
            'THREE_WHITE_SOLDIERS': self._pattern_three_white_soldiers,
            'THREE_BLACK_CROWS': self._pattern_three_black_crows,
            'SHOOTING_STAR': self._pattern_shooting_star,
            'HANGING_MAN': self._pattern_hanging_man,
            
            # Price Action
            'PREV_DAY_HIGH': self._prev_day_high,
            'PREV_DAY_LOW': self._prev_day_low,
            'PREV_DAY_CLOSE': self._prev_day_close,
            'DAY_CHANGE_PCT': self._day_change_pct,
            'GAP_PCT': self._gap_pct,
            'HIGH_OF_N': self._high_of_n,
            'LOW_OF_N': self._low_of_n,
            
            # Options (these come from external data, not calculated)
            'DELTA': self._options_delta,
            'GAMMA': self._options_gamma,
            'THETA': self._options_theta,
            'VEGA': self._options_vega,
            'IV': self._options_iv,
            'IV_RANK': self._options_iv_rank,
            'OI': self._options_oi,
            'OI_CHANGE': self._options_oi_change,
            'OI_CHANGE_PCT': self._options_oi_change_pct,
            'PCR': self._options_pcr,
            'VOLUME_OI_RATIO': self._options_volume_oi_ratio,
        }
    
    def _register_operators(self) -> dict[str, Callable]:
        """Register comparison operators."""
        return {
            'gt': lambda a, b: a > b,
            'gte': lambda a, b: a >= b,
            'lt': lambda a, b: a < b,
            'lte': lambda a, b: a <= b,
            'eq': lambda a, b: abs(a - b) < 0.0001,
            'neq': lambda a, b: abs(a - b) >= 0.0001,
            'crosses_above': self._crosses_above,
            'crosses_below': self._crosses_below,
        }
    
    # ============================================
    # MAIN CALCULATION METHODS
    # ============================================
    
    def _resolve_indicator(self, code: str) -> str:
        """Resolve frontend indicator code to backend code."""
        return self.INDICATOR_ALIASES.get(code, code)

    def _normalize_params(self, indicator_code: str, params: dict) -> dict:
        """Map frontend param names to backend param names."""
        resolved = self._resolve_indicator(indicator_code)
        aliases = self.PARAM_ALIASES.get(resolved, {})
        out = dict(params)
        for frontend_key, backend_key in aliases.items():
            if frontend_key in out and frontend_key != backend_key:
                out[backend_key] = out.pop(frontend_key)
        return out

    def calculate(self, indicator_code: str, df: pd.DataFrame, params: dict, options_data: dict = None) -> float:
        """
        Calculate an indicator value.
        
        Args:
            indicator_code: The indicator code (e.g., 'RSI', 'EMA') - frontend or backend
            df: OHLCV DataFrame with columns: open, high, low, close, volume
            params: Indicator parameters (e.g., {'period': 14}) - frontend or backend names
            options_data: Optional dict with options-specific data (delta, gamma, etc.)
        
        Returns:
            The current (last) value of the indicator
        """
        resolved = self._resolve_indicator(indicator_code)
        if resolved not in self.indicators:
            raise ValueError(f"Unknown indicator: {indicator_code} (resolved: {resolved})")
        
        normalized = self._normalize_params(resolved, params or {})
        calculator = self.indicators[resolved]
        
        # Pass options_data for options indicators
        if resolved.startswith(('DELTA', 'GAMMA', 'THETA', 'VEGA', 'IV', 'OI', 'PCR', 'VOLUME_OI')):
            return calculator(df, normalized, options_data or {})
        
        return calculator(df, normalized)
    
    def calculate_series(self, indicator_code: str, df: pd.DataFrame, params: dict) -> pd.Series:
        """
        Calculate full indicator series (for crossover detection).
        """
        # This returns the full series, not just the last value
        # Implementation depends on indicator type
        pass
    
    def evaluate_condition(self, df: pd.DataFrame, condition: dict, options_data: dict = None) -> bool:
        """
        Evaluate a filter condition.
        
        Args:
            df: OHLCV DataFrame
            condition: {
                'left': {'type': 'indicator', 'indicator': 'RSI', 'params': {'period': 14}},
                'operator': 'gt',
                'right': {'type': 'number', 'value': 60}
            }
            options_data: Optional options-specific data
        
        Returns:
            True if condition is met, False otherwise
        """
        try:
            # Calculate left side
            left_val = self._get_value(df, condition['left'], options_data)
            
            # Calculate right side
            right_val = self._get_value(df, condition['right'], options_data)
            
            # Get operator
            operator = condition.get('operator', 'gt')
            if operator not in self.operators:
                raise ValueError(f"Unknown operator: {operator}")
            
            # For crossover operators, we need series data
            if operator in ('crosses_above', 'crosses_below'):
                left_series = self._get_series(df, condition['left'])
                right_series = self._get_series(df, condition['right'])
                return self.operators[operator](left_series, right_series)
            
            # Simple comparison
            return self.operators[operator](left_val, right_val)
            
        except Exception as e:
            logger.error(f"Error evaluating condition: {e}")
            return False
    
    def evaluate_filter_config(self, df: pd.DataFrame, filter_config: dict, options_data: dict = None) -> bool:
        """
        Evaluate complete filter configuration with groups.
        
        Args:
            df: OHLCV DataFrame
            filter_config: {
                'groups': [
                    {
                        'logic': 'AND',
                        'conditions': [...]
                    }
                ],
                'group_logic': 'AND'
            }
        """
        groups = filter_config.get('groups', [])
        group_logic = filter_config.get('group_logic', 'AND')
        
        group_results = []
        
        for group in groups:
            conditions = group.get('conditions', [])
            logic = group.get('logic', 'AND')
            
            condition_results = []
            for cond in conditions:
                result = self.evaluate_condition(df, cond, options_data)
                condition_results.append(result)
            
            if not condition_results:
                continue
                
            if logic == 'AND':
                group_results.append(all(condition_results))
            else:  # OR
                group_results.append(any(condition_results))
        
        if not group_results:
            return False
            
        if group_logic == 'AND':
            return all(group_results)
        else:  # OR
            return any(group_results)
    
    def _get_value(self, df: pd.DataFrame, value_spec: dict, options_data: dict = None) -> float:
        """Get a value from either an indicator or a number."""
        if value_spec['type'] == 'number':
            return float(value_spec.get('value', 0))
        elif value_spec['type'] == 'indicator':
            return self.calculate(
                value_spec['indicator'],
                df,
                value_spec.get('params', {}),
                options_data
            )
        else:
            raise ValueError(f"Unknown value type: {value_spec['type']}")
    
    def _get_series(self, df: pd.DataFrame, value_spec: dict) -> pd.Series:
        """Get a series for crossover detection."""
        if value_spec['type'] == 'number':
            return pd.Series([float(value_spec.get('value', 0))] * len(df))
        elif value_spec['type'] == 'indicator':
            # Return full series - implementation specific to each indicator
            # For now, simplified version
            return self._calculate_indicator_series(
                value_spec['indicator'],
                df,
                value_spec.get('params', {})
            )
        else:
            raise ValueError(f"Unknown value type: {value_spec['type']}")
    
    # ============================================
    # CROSSOVER OPERATORS
    # ============================================
    
    def _crosses_above(self, series_a: pd.Series, series_b: pd.Series) -> bool:
        """Check if series_a crosses above series_b."""
        if len(series_a) < 2 or len(series_b) < 2:
            return False
        return series_a.iloc[-2] <= series_b.iloc[-2] and series_a.iloc[-1] > series_b.iloc[-1]
    
    def _crosses_below(self, series_a: pd.Series, series_b: pd.Series) -> bool:
        """Check if series_a crosses below series_b."""
        if len(series_a) < 2 or len(series_b) < 2:
            return False
        return series_a.iloc[-2] >= series_b.iloc[-2] and series_a.iloc[-1] < series_b.iloc[-1]
    
    # ============================================
    # PRICE INDICATORS
    # ============================================
    
    def _price_open(self, df: pd.DataFrame, params: dict) -> float:
        return df['open'].iloc[-1]
    
    def _price_high(self, df: pd.DataFrame, params: dict) -> float:
        return df['high'].iloc[-1]
    
    def _price_low(self, df: pd.DataFrame, params: dict) -> float:
        return df['low'].iloc[-1]
    
    def _price_close(self, df: pd.DataFrame, params: dict) -> float:
        return df['close'].iloc[-1]
    
    def _vwap(self, df: pd.DataFrame, params: dict) -> float:
        if HAS_PANDAS_TA:
            vwap = ta.vwap(df['high'], df['low'], df['close'], df['volume'])
            return vwap.iloc[-1] if vwap is not None else df['close'].iloc[-1]
        # Manual VWAP
        typical_price = (df['high'] + df['low'] + df['close']) / 3
        vwap = (typical_price * df['volume']).cumsum() / df['volume'].cumsum()
        return vwap.iloc[-1]
    
    def _typical_price(self, df: pd.DataFrame, params: dict) -> float:
        return (df['high'].iloc[-1] + df['low'].iloc[-1] + df['close'].iloc[-1]) / 3
    
    # ============================================
    # MOVING AVERAGES
    # ============================================
    
    def _sma(self, df: pd.DataFrame, params: dict) -> float:
        period = params.get('period', 20)
        if HAS_PANDAS_TA:
            sma = ta.sma(df['close'], length=period)
            return sma.iloc[-1] if sma is not None else np.nan
        return df['close'].rolling(window=period).mean().iloc[-1]
    
    def _ema(self, df: pd.DataFrame, params: dict) -> float:
        period = params.get('period', 20)
        if HAS_PANDAS_TA:
            ema = ta.ema(df['close'], length=period)
            return ema.iloc[-1] if ema is not None else np.nan
        return df['close'].ewm(span=period, adjust=False).mean().iloc[-1]
    
    def _wma(self, df: pd.DataFrame, params: dict) -> float:
        period = params.get('period', 20)
        if HAS_PANDAS_TA:
            wma = ta.wma(df['close'], length=period)
            return wma.iloc[-1] if wma is not None else np.nan
        weights = np.arange(1, period + 1)
        return df['close'].rolling(window=period).apply(
            lambda x: np.dot(x, weights) / weights.sum(), raw=True
        ).iloc[-1]
    
    def _dema(self, df: pd.DataFrame, params: dict) -> float:
        period = params.get('period', 20)
        if HAS_PANDAS_TA:
            dema = ta.dema(df['close'], length=period)
            return dema.iloc[-1] if dema is not None else np.nan
        ema1 = df['close'].ewm(span=period, adjust=False).mean()
        ema2 = ema1.ewm(span=period, adjust=False).mean()
        dema = 2 * ema1 - ema2
        return dema.iloc[-1]
    
    def _tema(self, df: pd.DataFrame, params: dict) -> float:
        period = params.get('period', 20)
        if HAS_PANDAS_TA:
            tema = ta.tema(df['close'], length=period)
            return tema.iloc[-1] if tema is not None else np.nan
        ema1 = df['close'].ewm(span=period, adjust=False).mean()
        ema2 = ema1.ewm(span=period, adjust=False).mean()
        ema3 = ema2.ewm(span=period, adjust=False).mean()
        tema = 3 * ema1 - 3 * ema2 + ema3
        return tema.iloc[-1]
    
    def _hma(self, df: pd.DataFrame, params: dict) -> float:
        period = params.get('period', 20)
        if HAS_PANDAS_TA:
            hma = ta.hma(df['close'], length=period)
            return hma.iloc[-1] if hma is not None else np.nan
        # Manual HMA
        half_period = period // 2
        sqrt_period = int(np.sqrt(period))
        wma_half = df['close'].rolling(window=half_period).apply(
            lambda x: np.dot(x, np.arange(1, half_period + 1)) / np.arange(1, half_period + 1).sum(), raw=True
        )
        wma_full = df['close'].rolling(window=period).apply(
            lambda x: np.dot(x, np.arange(1, period + 1)) / np.arange(1, period + 1).sum(), raw=True
        )
        raw_hma = 2 * wma_half - wma_full
        hma = raw_hma.rolling(window=sqrt_period).apply(
            lambda x: np.dot(x, np.arange(1, sqrt_period + 1)) / np.arange(1, sqrt_period + 1).sum(), raw=True
        )
        return hma.iloc[-1]
    
    # ============================================
    # RSI
    # ============================================
    
    def _rsi(self, df: pd.DataFrame, params: dict) -> float:
        period = params.get('period', 14)
        if HAS_PANDAS_TA:
            rsi = ta.rsi(df['close'], length=period)
            return rsi.iloc[-1] if rsi is not None else np.nan
        # Manual RSI
        delta = df['close'].diff()
        gain = delta.where(delta > 0, 0).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi.iloc[-1]
    
    def _rsi_sma(self, df: pd.DataFrame, params: dict) -> float:
        """RSI smoothed with SMA."""
        rsi_period = params.get('rsi_period', 14)
        sma_period = params.get('sma_period', 14)
        
        if HAS_PANDAS_TA:
            rsi = ta.rsi(df['close'], length=rsi_period)
            if rsi is None:
                return np.nan
            rsi_sma = rsi.rolling(window=sma_period).mean()
            return rsi_sma.iloc[-1] if rsi_sma is not None else np.nan
        
        # Manual
        delta = df['close'].diff()
        gain = delta.where(delta > 0, 0).rolling(window=rsi_period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=rsi_period).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi.rolling(window=sma_period).mean().iloc[-1]
    
    # ============================================
    # STOCHASTIC
    # ============================================
    
    def _stochastic_k(self, df: pd.DataFrame, params: dict) -> float:
        k_period = params.get('k_period', 14)
        smooth = params.get('smooth', 3)
        
        if HAS_PANDAS_TA:
            stoch = ta.stoch(df['high'], df['low'], df['close'], k=k_period, smooth_k=smooth)
            if stoch is not None:
                k_col = [c for c in stoch.columns if 'K' in c][0]
                return stoch[k_col].iloc[-1]
            return np.nan
        
        # Manual
        lowest_low = df['low'].rolling(window=k_period).min()
        highest_high = df['high'].rolling(window=k_period).max()
        k = 100 * (df['close'] - lowest_low) / (highest_high - lowest_low)
        k_smooth = k.rolling(window=smooth).mean()
        return k_smooth.iloc[-1]
    
    def _stochastic_d(self, df: pd.DataFrame, params: dict) -> float:
        k_period = params.get('k_period', 14)
        d_period = params.get('d_period', 3)
        
        if HAS_PANDAS_TA:
            stoch = ta.stoch(df['high'], df['low'], df['close'], k=k_period, d=d_period)
            if stoch is not None:
                d_col = [c for c in stoch.columns if 'D' in c][0]
                return stoch[d_col].iloc[-1]
            return np.nan
        
        # Manual
        lowest_low = df['low'].rolling(window=k_period).min()
        highest_high = df['high'].rolling(window=k_period).max()
        k = 100 * (df['close'] - lowest_low) / (highest_high - lowest_low)
        d = k.rolling(window=d_period).mean()
        return d.iloc[-1]
    
    # ============================================
    # OTHER MOMENTUM
    # ============================================
    
    def _cci(self, df: pd.DataFrame, params: dict) -> float:
        period = params.get('period', 20)
        if HAS_PANDAS_TA:
            cci = ta.cci(df['high'], df['low'], df['close'], length=period)
            return cci.iloc[-1] if cci is not None else np.nan
        # Manual
        typical_price = (df['high'] + df['low'] + df['close']) / 3
        sma = typical_price.rolling(window=period).mean()
        mad = typical_price.rolling(window=period).apply(lambda x: np.abs(x - x.mean()).mean(), raw=True)
        cci = (typical_price - sma) / (0.015 * mad)
        return cci.iloc[-1]
    
    def _williams_r(self, df: pd.DataFrame, params: dict) -> float:
        period = params.get('period', 14)
        if HAS_PANDAS_TA:
            willr = ta.willr(df['high'], df['low'], df['close'], length=period)
            return willr.iloc[-1] if willr is not None else np.nan
        # Manual
        highest_high = df['high'].rolling(window=period).max()
        lowest_low = df['low'].rolling(window=period).min()
        willr = -100 * (highest_high - df['close']) / (highest_high - lowest_low)
        return willr.iloc[-1]
    
    def _mfi(self, df: pd.DataFrame, params: dict) -> float:
        period = params.get('period', 14)
        if HAS_PANDAS_TA:
            mfi = ta.mfi(df['high'], df['low'], df['close'], df['volume'], length=period)
            return mfi.iloc[-1] if mfi is not None else np.nan
        # Manual
        typical_price = (df['high'] + df['low'] + df['close']) / 3
        money_flow = typical_price * df['volume']
        positive_flow = money_flow.where(typical_price > typical_price.shift(1), 0)
        negative_flow = money_flow.where(typical_price < typical_price.shift(1), 0)
        positive_sum = positive_flow.rolling(window=period).sum()
        negative_sum = negative_flow.rolling(window=period).sum()
        mfi = 100 - (100 / (1 + positive_sum / negative_sum))
        return mfi.iloc[-1]
    
    def _roc(self, df: pd.DataFrame, params: dict) -> float:
        period = params.get('period', 10)
        if HAS_PANDAS_TA:
            roc = ta.roc(df['close'], length=period)
            return roc.iloc[-1] if roc is not None else np.nan
        return ((df['close'].iloc[-1] - df['close'].iloc[-period - 1]) / df['close'].iloc[-period - 1]) * 100
    
    def _momentum(self, df: pd.DataFrame, params: dict) -> float:
        period = params.get('period', 10)
        if HAS_PANDAS_TA:
            mom = ta.mom(df['close'], length=period)
            return mom.iloc[-1] if mom is not None else np.nan
        return df['close'].iloc[-1] - df['close'].iloc[-period - 1]
    
    # ============================================
    # MACD
    # ============================================
    
    def _macd_line(self, df: pd.DataFrame, params: dict) -> float:
        fast = params.get('fast', 12)
        slow = params.get('slow', 26)
        if HAS_PANDAS_TA:
            macd = ta.macd(df['close'], fast=fast, slow=slow)
            if macd is not None:
                macd_col = [c for c in macd.columns if 'MACD_' in c and 'h' not in c.lower() and 's' not in c.lower()][0]
                return macd[macd_col].iloc[-1]
            return np.nan
        # Manual
        ema_fast = df['close'].ewm(span=fast, adjust=False).mean()
        ema_slow = df['close'].ewm(span=slow, adjust=False).mean()
        return (ema_fast - ema_slow).iloc[-1]
    
    def _macd_signal(self, df: pd.DataFrame, params: dict) -> float:
        fast = params.get('fast', 12)
        slow = params.get('slow', 26)
        signal = params.get('signal', 9)
        if HAS_PANDAS_TA:
            macd = ta.macd(df['close'], fast=fast, slow=slow, signal=signal)
            if macd is not None:
                signal_col = [c for c in macd.columns if 's' in c.lower()][0]
                return macd[signal_col].iloc[-1]
            return np.nan
        # Manual
        ema_fast = df['close'].ewm(span=fast, adjust=False).mean()
        ema_slow = df['close'].ewm(span=slow, adjust=False).mean()
        macd_line = ema_fast - ema_slow
        return macd_line.ewm(span=signal, adjust=False).mean().iloc[-1]
    
    def _macd_histogram(self, df: pd.DataFrame, params: dict) -> float:
        fast = params.get('fast', 12)
        slow = params.get('slow', 26)
        signal = params.get('signal', 9)
        if HAS_PANDAS_TA:
            macd = ta.macd(df['close'], fast=fast, slow=slow, signal=signal)
            if macd is not None:
                hist_col = [c for c in macd.columns if 'h' in c.lower()][0]
                return macd[hist_col].iloc[-1]
            return np.nan
        # Manual
        ema_fast = df['close'].ewm(span=fast, adjust=False).mean()
        ema_slow = df['close'].ewm(span=slow, adjust=False).mean()
        macd_line = ema_fast - ema_slow
        signal_line = macd_line.ewm(span=signal, adjust=False).mean()
        return (macd_line - signal_line).iloc[-1]
    
    # ============================================
    # ADX
    # ============================================
    
    def _adx(self, df: pd.DataFrame, params: dict) -> float:
        period = params.get('period', 14)
        if HAS_PANDAS_TA:
            adx = ta.adx(df['high'], df['low'], df['close'], length=period)
            if adx is not None:
                adx_col = [c for c in adx.columns if 'ADX' in c and 'DM' not in c][0]
                return adx[adx_col].iloc[-1]
            return np.nan
        # Simplified manual ADX
        return np.nan  # Complex calculation, recommend using pandas_ta
    
    def _plus_di(self, df: pd.DataFrame, params: dict) -> float:
        period = params.get('period', 14)
        if HAS_PANDAS_TA:
            adx = ta.adx(df['high'], df['low'], df['close'], length=period)
            if adx is not None:
                di_col = [c for c in adx.columns if 'DMP' in c][0]
                return adx[di_col].iloc[-1]
            return np.nan
        return np.nan
    
    def _minus_di(self, df: pd.DataFrame, params: dict) -> float:
        period = params.get('period', 14)
        if HAS_PANDAS_TA:
            adx = ta.adx(df['high'], df['low'], df['close'], length=period)
            if adx is not None:
                di_col = [c for c in adx.columns if 'DMN' in c][0]
                return adx[di_col].iloc[-1]
            return np.nan
        return np.nan
    
    # ============================================
    # SUPERTREND
    # ============================================
    
    def _supertrend(self, df: pd.DataFrame, params: dict) -> float:
        period = params.get('period', 10)
        multiplier = params.get('multiplier', 3)
        if HAS_PANDAS_TA:
            st = ta.supertrend(df['high'], df['low'], df['close'], length=period, multiplier=multiplier)
            if st is not None:
                st_col = [c for c in st.columns if 'SUPERT_' in c and 'd' not in c.lower()][0]
                return st[st_col].iloc[-1]
            return np.nan
        return np.nan
    
    def _supertrend_direction(self, df: pd.DataFrame, params: dict) -> float:
        """Returns 1 for bullish, -1 for bearish."""
        period = params.get('period', 10)
        multiplier = params.get('multiplier', 3)
        if HAS_PANDAS_TA:
            st = ta.supertrend(df['high'], df['low'], df['close'], length=period, multiplier=multiplier)
            if st is not None:
                dir_col = [c for c in st.columns if 'd' in c.lower()][0]
                return st[dir_col].iloc[-1]
            return np.nan
        return np.nan
    
    # ============================================
    # VOLATILITY
    # ============================================
    
    def _atr(self, df: pd.DataFrame, params: dict) -> float:
        period = params.get('period', 14)
        if HAS_PANDAS_TA:
            atr = ta.atr(df['high'], df['low'], df['close'], length=period)
            return atr.iloc[-1] if atr is not None else np.nan
        # Manual
        high_low = df['high'] - df['low']
        high_close = abs(df['high'] - df['close'].shift(1))
        low_close = abs(df['low'] - df['close'].shift(1))
        tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
        return tr.rolling(window=period).mean().iloc[-1]
    
    def _bb_upper(self, df: pd.DataFrame, params: dict) -> float:
        period = params.get('period', 20)
        std = params.get('std', 2)
        if HAS_PANDAS_TA:
            bb = ta.bbands(df['close'], length=period, std=std)
            if bb is not None:
                upper_col = [c for c in bb.columns if 'BBU' in c][0]
                return bb[upper_col].iloc[-1]
            return np.nan
        sma = df['close'].rolling(window=period).mean()
        std_dev = df['close'].rolling(window=period).std()
        return (sma + std * std_dev).iloc[-1]
    
    def _bb_middle(self, df: pd.DataFrame, params: dict) -> float:
        period = params.get('period', 20)
        if HAS_PANDAS_TA:
            bb = ta.bbands(df['close'], length=period)
            if bb is not None:
                mid_col = [c for c in bb.columns if 'BBM' in c][0]
                return bb[mid_col].iloc[-1]
            return np.nan
        return df['close'].rolling(window=period).mean().iloc[-1]
    
    def _bb_lower(self, df: pd.DataFrame, params: dict) -> float:
        period = params.get('period', 20)
        std = params.get('std', 2)
        if HAS_PANDAS_TA:
            bb = ta.bbands(df['close'], length=period, std=std)
            if bb is not None:
                lower_col = [c for c in bb.columns if 'BBL' in c][0]
                return bb[lower_col].iloc[-1]
            return np.nan
        sma = df['close'].rolling(window=period).mean()
        std_dev = df['close'].rolling(window=period).std()
        return (sma - std * std_dev).iloc[-1]
    
    def _bb_percent_b(self, df: pd.DataFrame, params: dict) -> float:
        period = params.get('period', 20)
        std = params.get('std', 2)
        if HAS_PANDAS_TA:
            bb = ta.bbands(df['close'], length=period, std=std)
            if bb is not None:
                b_col = [c for c in bb.columns if 'BBB' in c][0]
                return bb[b_col].iloc[-1]
            return np.nan
        sma = df['close'].rolling(window=period).mean()
        std_dev = df['close'].rolling(window=period).std()
        upper = sma + std * std_dev
        lower = sma - std * std_dev
        return ((df['close'] - lower) / (upper - lower)).iloc[-1]
    
    def _bb_width(self, df: pd.DataFrame, params: dict) -> float:
        period = params.get('period', 20)
        std = params.get('std', 2)
        if HAS_PANDAS_TA:
            bb = ta.bbands(df['close'], length=period, std=std)
            if bb is not None:
                width_col = [c for c in bb.columns if 'BBW' in c][0]
                return bb[width_col].iloc[-1]
            return np.nan
        sma = df['close'].rolling(window=period).mean()
        std_dev = df['close'].rolling(window=period).std()
        upper = sma + std * std_dev
        lower = sma - std * std_dev
        return ((upper - lower) / sma).iloc[-1]
    
    # ============================================
    # VOLUME
    # ============================================
    
    def _volume(self, df: pd.DataFrame, params: dict) -> float:
        return df['volume'].iloc[-1]
    
    def _volume_sma(self, df: pd.DataFrame, params: dict) -> float:
        period = params.get('period', 20)
        return df['volume'].rolling(window=period).mean().iloc[-1]
    
    def _obv(self, df: pd.DataFrame, params: dict) -> float:
        if HAS_PANDAS_TA:
            obv = ta.obv(df['close'], df['volume'])
            return obv.iloc[-1] if obv is not None else np.nan
        # Manual
        direction = np.sign(df['close'].diff())
        obv = (direction * df['volume']).cumsum()
        return obv.iloc[-1]
    
    # ============================================
    # CANDLESTICK PATTERNS
    # ============================================
    
    def _pattern_doji(self, df: pd.DataFrame, params: dict) -> float:
        last = df.iloc[-1]
        body = abs(last['close'] - last['open'])
        range_ = last['high'] - last['low']
        return 1.0 if range_ > 0 and body <= range_ * 0.1 else 0.0
    
    def _pattern_hammer(self, df: pd.DataFrame, params: dict) -> float:
        last = df.iloc[-1]
        body = abs(last['close'] - last['open'])
        lower_shadow = min(last['open'], last['close']) - last['low']
        upper_shadow = last['high'] - max(last['open'], last['close'])
        return 1.0 if lower_shadow > 2 * body and upper_shadow < body else 0.0
    
    def _pattern_inverted_hammer(self, df: pd.DataFrame, params: dict) -> float:
        last = df.iloc[-1]
        body = abs(last['close'] - last['open'])
        lower_shadow = min(last['open'], last['close']) - last['low']
        upper_shadow = last['high'] - max(last['open'], last['close'])
        return 1.0 if upper_shadow > 2 * body and lower_shadow < body else 0.0
    
    def _pattern_bullish_engulfing(self, df: pd.DataFrame, params: dict) -> float:
        if len(df) < 2:
            return 0.0
        prev = df.iloc[-2]
        curr = df.iloc[-1]
        prev_bearish = prev['close'] < prev['open']
        curr_bullish = curr['close'] > curr['open']
        engulfs = curr['open'] < prev['close'] and curr['close'] > prev['open']
        return 1.0 if prev_bearish and curr_bullish and engulfs else 0.0
    
    def _pattern_bearish_engulfing(self, df: pd.DataFrame, params: dict) -> float:
        if len(df) < 2:
            return 0.0
        prev = df.iloc[-2]
        curr = df.iloc[-1]
        prev_bullish = prev['close'] > prev['open']
        curr_bearish = curr['close'] < curr['open']
        engulfs = curr['open'] > prev['close'] and curr['close'] < prev['open']
        return 1.0 if prev_bullish and curr_bearish and engulfs else 0.0
    
    def _pattern_morning_star(self, df: pd.DataFrame, params: dict) -> float:
        if len(df) < 3:
            return 0.0
        first = df.iloc[-3]
        second = df.iloc[-2]
        third = df.iloc[-1]
        
        first_bearish = first['close'] < first['open']
        second_small = abs(second['close'] - second['open']) < abs(first['close'] - first['open']) * 0.3
        third_bullish = third['close'] > third['open']
        third_closes_above = third['close'] > (first['open'] + first['close']) / 2
        
        return 1.0 if first_bearish and second_small and third_bullish and third_closes_above else 0.0
    
    def _pattern_evening_star(self, df: pd.DataFrame, params: dict) -> float:
        if len(df) < 3:
            return 0.0
        first = df.iloc[-3]
        second = df.iloc[-2]
        third = df.iloc[-1]
        
        first_bullish = first['close'] > first['open']
        second_small = abs(second['close'] - second['open']) < abs(first['close'] - first['open']) * 0.3
        third_bearish = third['close'] < third['open']
        third_closes_below = third['close'] < (first['open'] + first['close']) / 2
        
        return 1.0 if first_bullish and second_small and third_bearish and third_closes_below else 0.0
    
    def _pattern_three_white_soldiers(self, df: pd.DataFrame, params: dict) -> float:
        if len(df) < 3:
            return 0.0
        candles = df.iloc[-3:]
        all_bullish = all(c['close'] > c['open'] for _, c in candles.iterrows())
        closes_ascending = candles['close'].is_monotonic_increasing
        return 1.0 if all_bullish and closes_ascending else 0.0
    
    def _pattern_three_black_crows(self, df: pd.DataFrame, params: dict) -> float:
        if len(df) < 3:
            return 0.0
        candles = df.iloc[-3:]
        all_bearish = all(c['close'] < c['open'] for _, c in candles.iterrows())
        closes_descending = candles['close'].is_monotonic_decreasing
        return 1.0 if all_bearish and closes_descending else 0.0
    
    def _pattern_shooting_star(self, df: pd.DataFrame, params: dict) -> float:
        last = df.iloc[-1]
        body = abs(last['close'] - last['open'])
        upper_shadow = last['high'] - max(last['open'], last['close'])
        lower_shadow = min(last['open'], last['close']) - last['low']
        return 1.0 if upper_shadow > 2 * body and lower_shadow < body * 0.5 else 0.0
    
    def _pattern_hanging_man(self, df: pd.DataFrame, params: dict) -> float:
        # Same as hammer but in an uptrend context
        return self._pattern_hammer(df, params)
    
    # ============================================
    # PRICE ACTION
    # ============================================
    
    def _prev_day_high(self, df: pd.DataFrame, params: dict) -> float:
        if len(df) < 2:
            return np.nan
        return df['high'].iloc[-2]
    
    def _prev_day_low(self, df: pd.DataFrame, params: dict) -> float:
        if len(df) < 2:
            return np.nan
        return df['low'].iloc[-2]
    
    def _prev_day_close(self, df: pd.DataFrame, params: dict) -> float:
        if len(df) < 2:
            return np.nan
        return df['close'].iloc[-2]
    
    def _day_change_pct(self, df: pd.DataFrame, params: dict) -> float:
        if len(df) < 2:
            return 0.0
        prev_close = df['close'].iloc[-2]
        curr_close = df['close'].iloc[-1]
        return ((curr_close - prev_close) / prev_close) * 100
    
    def _gap_pct(self, df: pd.DataFrame, params: dict) -> float:
        if len(df) < 2:
            return 0.0
        prev_close = df['close'].iloc[-2]
        curr_open = df['open'].iloc[-1]
        return ((curr_open - prev_close) / prev_close) * 100
    
    def _high_of_n(self, df: pd.DataFrame, params: dict) -> float:
        period = params.get('period', 20)
        return df['high'].iloc[-period:].max()
    
    def _low_of_n(self, df: pd.DataFrame, params: dict) -> float:
        period = params.get('period', 20)
        return df['low'].iloc[-period:].min()
    
    # ============================================
    # OPTIONS (External Data)
    # ============================================
    
    def _options_delta(self, df: pd.DataFrame, params: dict, options_data: dict) -> float:
        return options_data.get('delta', np.nan)
    
    def _options_gamma(self, df: pd.DataFrame, params: dict, options_data: dict) -> float:
        return options_data.get('gamma', np.nan)
    
    def _options_theta(self, df: pd.DataFrame, params: dict, options_data: dict) -> float:
        return options_data.get('theta', np.nan)
    
    def _options_vega(self, df: pd.DataFrame, params: dict, options_data: dict) -> float:
        return options_data.get('vega', np.nan)
    
    def _options_iv(self, df: pd.DataFrame, params: dict, options_data: dict) -> float:
        return options_data.get('iv', np.nan)
    
    def _options_iv_rank(self, df: pd.DataFrame, params: dict, options_data: dict) -> float:
        return options_data.get('iv_rank', np.nan)
    
    def _options_oi(self, df: pd.DataFrame, params: dict, options_data: dict) -> float:
        return options_data.get('oi', np.nan)
    
    def _options_oi_change(self, df: pd.DataFrame, params: dict, options_data: dict) -> float:
        return options_data.get('oi_change', np.nan)
    
    def _options_oi_change_pct(self, df: pd.DataFrame, params: dict, options_data: dict) -> float:
        return options_data.get('oi_change_pct', np.nan)
    
    def _options_pcr(self, df: pd.DataFrame, params: dict, options_data: dict) -> float:
        return options_data.get('pcr', np.nan)
    
    def _options_volume_oi_ratio(self, df: pd.DataFrame, params: dict, options_data: dict) -> float:
        return options_data.get('volume_oi_ratio', np.nan)
    
    # ============================================
    # HELPER: Calculate full series for crossovers
    # ============================================
    
    def _calculate_indicator_series(self, indicator_code: str, df: pd.DataFrame, params: dict) -> pd.Series:
        """Calculate full indicator series for crossover detection."""
        if indicator_code == 'RSI':
            period = params.get('period', 14)
            if HAS_PANDAS_TA:
                return ta.rsi(df['close'], length=period)
            delta = df['close'].diff()
            gain = delta.where(delta > 0, 0).rolling(window=period).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
            rs = gain / loss
            return 100 - (100 / (1 + rs))
        
        elif indicator_code == 'RSI_SMA':
            rsi_period = params.get('rsi_period', 14)
            sma_period = params.get('sma_period', 14)
            if HAS_PANDAS_TA:
                rsi = ta.rsi(df['close'], length=rsi_period)
                return rsi.rolling(window=sma_period).mean()
            return pd.Series([np.nan] * len(df))
        
        elif indicator_code in ('SMA', 'EMA'):
            period = params.get('period', 20)
            if indicator_code == 'SMA':
                return df['close'].rolling(window=period).mean()
            else:
                return df['close'].ewm(span=period, adjust=False).mean()
        
        elif indicator_code == 'CLOSE':
            return df['close']
        
        # Add more series calculations as needed
        return pd.Series([np.nan] * len(df))


# ============================================
# CONVENIENCE FUNCTIONS
# ============================================

def create_filter_engine() -> FilterEngine:
    """Create a new FilterEngine instance."""
    return FilterEngine()


def evaluate_strike(
    df: pd.DataFrame,
    filter_config: dict,
    options_data: dict = None,
    engine: FilterEngine = None
) -> bool:
    """
    Evaluate filter conditions for a single strike.
    
    Args:
        df: OHLCV DataFrame for the strike
        filter_config: Filter configuration dict
        options_data: Optional options data (delta, gamma, etc.)
        engine: Optional FilterEngine instance (creates new if not provided)
    
    Returns:
        True if all conditions are met
    """
    if engine is None:
        engine = FilterEngine()
    return engine.evaluate_filter_config(df, filter_config, options_data)
