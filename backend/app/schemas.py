from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field


class RuleIn(BaseModel):
    field: Literal["rsi_14", "ema_20", "macd", "macd_signal", "iv", "oi", "pcr", "delta", "gamma", "oi_change_pct", "volume", "moneyness", "expiry_days"]
    operator: Literal[">", "<", ">=", "<=", "==", "crosses_above", "crosses_below"]
    value: float


class ConditionGroupIn(BaseModel):
    logical_operator: Literal["AND", "OR"] = "AND"
    rules: list[RuleIn] = Field(default_factory=list)


class TechnicalScanRuleIn(BaseModel):
    indicator: str = "rsi_14"
    operator: Literal[">", "<", ">=", "<=", "=="] = ">"
    value: float


class TechnicalScanRequest(BaseModel):
    underlyings: list[str] | None = None  # None = all F&O (NIFTY, BANKNIFTY, FINNIFTY)
    expiry: str | None = None  # None = all expiries
    timeframe: str = "5m"  # 1m, 3m, 5m, 15m, 30m, 1h, 4h, 1d per Fyers API
    rules: list[TechnicalScanRuleIn] = Field(default_factory=list)
    filter_config: dict | None = None  # Advanced: groups + conditions (synced with ScreenerBuilder)
    candle_days: int = 5
    max_strikes_per_underlying: int = 30


class TechnicalScanResultOut(BaseModel):
    symbol: str
    underlying: str
    strike_price: float | None
    option_type: str | None
    ltp: float | None
    oi: int | None
    expiry: str | None = None
    indicators: dict[str, float | None]


class TechnicalScanResponse(BaseModel):
    results: list[TechnicalScanResultOut]
    count: int


class ScanRequest(BaseModel):
    timeframe: Literal["1m", "5m", "15m"] = "5m"
    underlying: str | None = None
    limit: int = 500
    rules: list[RuleIn] = Field(default_factory=list)
    groups: list[ConditionGroupIn] = Field(default_factory=list)


class CursorPage(BaseModel):
    items: list[dict[str, Any]]
    next_cursor: str | None = None


class ScanResultOut(BaseModel):
    token: str
    matched: bool
    reason: str


class ScanResponse(BaseModel):
    scan_id: str
    created_at: datetime
    results: list[ScanResultOut]


class ScreenerIn(BaseModel):
    user_id: str
    name: str
    description: str | None = None
    underlying: str | None = None
    timeframe: Literal["1m", "5m", "15m"] = "5m"
    groups: list[ConditionGroupIn] = Field(default_factory=list)


class ScreenerUpdateIn(BaseModel):
    name: str | None = None
    description: str | None = None
    underlying: str | None = None
    timeframe: Literal["1m", "5m", "15m"] | None = None
    groups: list[ConditionGroupIn] | None = None


class ScreenerOut(BaseModel):
    id: str
    user_id: str
    name: str
    description: str | None = None
    underlying: str | None = None
    timeframe: str
    groups: list[ConditionGroupIn] = Field(default_factory=list)
    created_at: str


class StrategyIn(BaseModel):
    user_id: str
    name: str
    rules: list[RuleIn]


class WorkspaceIn(BaseModel):
    user_id: str
    name: str
    layout: dict[str, Any] = Field(default_factory=dict)


class AlertIn(BaseModel):
    user_id: str
    name: str
    rule: RuleIn


class InstrumentOut(BaseModel):
    token: str


class StrikeOut(BaseModel):
    token: str


class StrikeCandleOut(BaseModel):
    timestamp: str
    open: float
    high: float
    low: float
    close: float
    volume: int


class ChartOut(BaseModel):
    token: str
    timeframe: str
    candles: list[dict[str, Any]]


class TickIn(BaseModel):
    token: str
    ltp: float
    volume: int = 0
    timeframe: Literal["1m", "5m", "15m"] = "1m"
    ts: datetime | None = None


class TickIngestOut(BaseModel):
    ingested: bool
    candle_persisted: bool


class StrategyOut(BaseModel):
    id: str
    owner_id: str
    name: str
    rules: list[dict[str, Any]]


class WorkspaceOut(BaseModel):
    id: str
    owner_id: str
    name: str
    layout: dict[str, Any]


class AlertOut(BaseModel):
    id: str
    user_id: str
    name: str
    rule: dict[str, Any]


class AuditEventOut(BaseModel):
    id: str
    entity_type: str
    entity_id: str
    action: str
    actor_id: str
    payload: dict[str, Any]
    created_at: str


class StockOut(BaseModel):
    symbol: str
    price: float
    change_percent: float


class AiInsight(BaseModel):
    thesis: str
    confidence: float
    factors: list[dict[str, Any]]
    risk_flags: list[str]
    sources: list[dict[str, Any]]


class SignalOut(BaseModel):
    id: str
    token: str
    timeframe: str
    signal_type: str
    indicator: str
    message: str
    created_at: str


class OptionsChainRowOut(BaseModel):
    underlying: str
    expiry: str
    strike_price: float
    call_token: str | None = None
    call_symbol: str | None = None
    call_oi: int | None = None
    call_iv: float | None = None
    call_ltp: float | None = None
    put_token: str | None = None
    put_symbol: str | None = None
    put_oi: int | None = None
    put_iv: float | None = None
    put_ltp: float | None = None
    put_call_ratio: float | None = None
    total_oi_change: int | None = None
    lot_size: int
    fetched_at: str


class OptionsChainMetricsOut(BaseModel):
    underlying: str
    expiry: str
    strikes: int
    total_call_oi: int
    total_put_oi: int
    put_call_ratio: float | None = None
    total_oi_change: int


class OptionsGreeksOut(BaseModel):
    option_type: str
    spot: float
    strike: float
    time_to_expiry_years: float
    risk_free_rate: float
    volatility: float
    delta: float
    gamma: float
    theta: float
    vega: float
    rho: float


class StrikeGreeksOut(BaseModel):
    underlying: str
    expiry: str
    symbol: str
    token: str
    option_type: str
    strike_price: float
    spot: float
    time_to_expiry_years: float
    risk_free_rate: float
    volatility: float
    delta: float
    gamma: float
    theta: float
    vega: float
    rho: float
    calculated_at: str


class OIHeatmapPointOut(BaseModel):
    strike_price: float
    total_oi: int
    total_oi_change: int
    total_oi_change_pct: float
    recorded_at: str


class CorrelationOut(BaseModel):
    token_a: str
    token_b: str
    timeframe: str
    samples: int
    correlation: float | None = None


class SentimentOut(BaseModel):
    symbol: str
    sentiment: Literal["bullish", "bearish", "neutral"]
    score: float
    summary: str


class PatternSignalOut(BaseModel):
    pattern: str
    direction: Literal["bullish", "bearish", "neutral"]
    confidence: float
    description: str


class PatternOut(BaseModel):
    symbol: str
    timeframe: str
    signals: list[PatternSignalOut] = Field(default_factory=list)


class WatchlistIn(BaseModel):
    user_id: str
    name: str


class WatchlistOut(BaseModel):
    id: str
    user_id: str
    name: str
    created_at: str
    tokens: list[str] = Field(default_factory=list)


class WatchlistItemIn(BaseModel):
    token: str


class FavoriteIn(BaseModel):
    user_id: str
    token: str


class FavoriteOut(BaseModel):
    id: str
    user_id: str
    token: str
    created_at: str


class NotificationPreferenceIn(BaseModel):
    user_id: str
    channel: Literal["email", "push"]
    destination: str
    enabled: bool = True


class NotificationPreferenceOut(BaseModel):
    id: str
    user_id: str
    channel: str
    destination: str
    enabled: bool
    created_at: str


class NotificationOutboxOut(BaseModel):
    id: str
    user_id: str
    channel: str
    destination: str
    subject: str
    body: str
    status: str
    error_message: str | None = None
    created_at: str
    sent_at: str | None = None


class MarketplacePublishIn(BaseModel):
    strategy_id: str
    owner_id: str
    title: str
    description: str
    tags: list[str] = Field(default_factory=list)


class MarketplaceStrategyOut(BaseModel):
    id: str
    strategy_id: str
    owner_id: str
    title: str
    description: str
    tags: list[str]
    share_code: str
    created_at: str


class UserProfileIn(BaseModel):
    email: str | None = None
    display_name: str | None = None


class UserProfileOut(BaseModel):
    id: str
    clerk_user_id: str
    email: str | None = None
    display_name: str | None = None
    created_at: str
    updated_at: str


class UserPreferenceIn(BaseModel):
    default_timeframe: Literal["1m", "5m", "15m"] = "5m"
    default_indicator: Literal["rsi_14", "ema_20", "macd", "macd_signal"] = "rsi_14"
    theme: Literal["dark", "light"] = "dark"


class UserPreferenceOut(BaseModel):
    id: str
    clerk_user_id: str
    default_timeframe: str
    default_indicator: str
    theme: str
    created_at: str
    updated_at: str
