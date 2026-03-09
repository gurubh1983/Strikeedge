from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import Float, Integer, JSON, DateTime, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Base(DeclarativeBase):
    pass


class InstrumentModel(Base):
    __tablename__ = "instruments"

    token: Mapped[str] = mapped_column(String(64), primary_key=True)
    symbol: Mapped[str] = mapped_column(String(128), index=True)
    name: Mapped[str] = mapped_column(String(128), index=True)
    exchange: Mapped[str] = mapped_column(String(16), index=True, default="NFO")
    instrument_type: Mapped[str] = mapped_column(String(32), index=True)
    underlying: Mapped[str] = mapped_column(String(64), index=True)
    option_type: Mapped[str | None] = mapped_column(String(8), nullable=True)  # CE/PE
    strike_price: Mapped[float | None] = mapped_column(Float, nullable=True)
    expiry: Mapped[str | None] = mapped_column(String(32), nullable=True)
    lot_size: Mapped[int] = mapped_column(Integer, default=1)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)


class CandleModel(Base):
    __tablename__ = "candles"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    token: Mapped[str] = mapped_column(String(64), index=True)
    timeframe: Mapped[str] = mapped_column(String(8), index=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    open: Mapped[float] = mapped_column(Float)
    high: Mapped[float] = mapped_column(Float)
    low: Mapped[float] = mapped_column(Float)
    close: Mapped[float] = mapped_column(Float)
    volume: Mapped[int] = mapped_column(Integer, default=0)


class StrikeCandleModel(Base):
    __tablename__ = "strike_candles"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    symbol: Mapped[str] = mapped_column(String(128), index=True)
    token: Mapped[str] = mapped_column(String(64), index=True)
    timeframe: Mapped[str] = mapped_column(String(8), index=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    open: Mapped[float] = mapped_column(Float)
    high: Mapped[float] = mapped_column(Float)
    low: Mapped[float] = mapped_column(Float)
    close: Mapped[float] = mapped_column(Float)
    volume: Mapped[int] = mapped_column(Integer, default=0)


class IndicatorValueModel(Base):
    __tablename__ = "indicator_values"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    token: Mapped[str] = mapped_column(String(64), index=True)
    timeframe: Mapped[str] = mapped_column(String(8), index=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    rsi_14: Mapped[float | None] = mapped_column(Float, nullable=True)
    ema_20: Mapped[float | None] = mapped_column(Float, nullable=True)
    macd: Mapped[float | None] = mapped_column(Float, nullable=True)
    macd_signal: Mapped[float | None] = mapped_column(Float, nullable=True)
    iv: Mapped[float | None] = mapped_column(Float, nullable=True)
    oi: Mapped[int | None] = mapped_column(Integer, nullable=True)


class StrategyModel(Base):
    __tablename__ = "strategies"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    owner_id: Mapped[str] = mapped_column(String(128), index=True)
    name: Mapped[str] = mapped_column(String(256))
    rules: Mapped[list] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)


class WorkspaceModel(Base):
    __tablename__ = "workspaces"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    owner_id: Mapped[str] = mapped_column(String(128), index=True)
    name: Mapped[str] = mapped_column(String(256))
    layout: Mapped[dict] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)


class AlertModel(Base):
    __tablename__ = "alerts"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    user_id: Mapped[str] = mapped_column(String(128), index=True)
    name: Mapped[str] = mapped_column(String(256))
    rule: Mapped[dict] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)


class AuditEventModel(Base):
    __tablename__ = "audit_events"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    entity_type: Mapped[str] = mapped_column(String(64), index=True)
    entity_id: Mapped[str] = mapped_column(String(64), index=True)
    action: Mapped[str] = mapped_column(String(64))
    actor_id: Mapped[str] = mapped_column(String(128), index=True)
    payload: Mapped[dict] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)


class IdempotencyRecordModel(Base):
    __tablename__ = "idempotency_records"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    actor_id: Mapped[str] = mapped_column(String(128), index=True)
    idempotency_key: Mapped[str] = mapped_column(String(256), index=True)
    endpoint: Mapped[str] = mapped_column(String(256), index=True)
    response_payload: Mapped[dict] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)


class ScanJobModel(Base):
    __tablename__ = "scan_jobs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    timeframe: Mapped[str] = mapped_column(String(8), index=True)
    rules: Mapped[list] = mapped_column(JSON)
    results: Mapped[list] = mapped_column(JSON)
    status: Mapped[str] = mapped_column(String(32), default="completed", index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)


class ScreenerModel(Base):
    __tablename__ = "screeners"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    user_id: Mapped[str] = mapped_column(String(128), index=True)
    name: Mapped[str] = mapped_column(String(256), index=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    timeframe: Mapped[str] = mapped_column(String(8), default="5m")
    conditions: Mapped[list] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)


class ScanResultModel(Base):
    __tablename__ = "scan_results"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    scan_id: Mapped[str] = mapped_column(String(36), index=True)
    token: Mapped[str] = mapped_column(String(64), index=True)
    matched: Mapped[int] = mapped_column(Integer, default=0)
    reason: Mapped[str] = mapped_column(String(256))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)


class AgentJobModel(Base):
    __tablename__ = "agent_jobs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    user_id: Mapped[str] = mapped_column(String(128), index=True)
    job_type: Mapped[str] = mapped_column(String(64), index=True)
    status: Mapped[str] = mapped_column(String(32), default="pending", index=True)
    request_payload: Mapped[dict] = mapped_column(JSON)
    output_payload: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)


class SignalEventModel(Base):
    __tablename__ = "signal_events"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    token: Mapped[str] = mapped_column(String(64), index=True)
    timeframe: Mapped[str] = mapped_column(String(8), index=True)
    signal_type: Mapped[str] = mapped_column(String(64), index=True)
    indicator: Mapped[str] = mapped_column(String(64), index=True)
    message: Mapped[str] = mapped_column(String(256))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, index=True)


class OptionsChainModel(Base):
    __tablename__ = "options_chain"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    underlying: Mapped[str] = mapped_column(String(64), index=True)
    expiry: Mapped[str] = mapped_column(String(32), index=True)
    strike_price: Mapped[float] = mapped_column(Float, index=True)
    call_token: Mapped[str | None] = mapped_column(String(64), nullable=True)
    call_symbol: Mapped[str | None] = mapped_column(String(128), nullable=True)
    call_oi: Mapped[int | None] = mapped_column(Integer, nullable=True)
    call_iv: Mapped[float | None] = mapped_column(Float, nullable=True)
    put_token: Mapped[str | None] = mapped_column(String(64), nullable=True)
    put_symbol: Mapped[str | None] = mapped_column(String(128), nullable=True)
    put_oi: Mapped[int | None] = mapped_column(Integer, nullable=True)
    put_iv: Mapped[float | None] = mapped_column(Float, nullable=True)
    put_call_ratio: Mapped[float | None] = mapped_column(Float, nullable=True)
    total_oi_change: Mapped[int | None] = mapped_column(Integer, nullable=True)
    lot_size: Mapped[int] = mapped_column(Integer, default=1)
    fetched_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, index=True)


class StrikeGreeksModel(Base):
    __tablename__ = "strike_greeks"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    underlying: Mapped[str] = mapped_column(String(64), index=True)
    expiry: Mapped[str] = mapped_column(String(32), index=True)
    symbol: Mapped[str] = mapped_column(String(128), index=True)
    token: Mapped[str] = mapped_column(String(64), index=True)
    option_type: Mapped[str] = mapped_column(String(8), index=True)
    strike_price: Mapped[float] = mapped_column(Float, index=True)
    spot: Mapped[float] = mapped_column(Float)
    time_to_expiry_years: Mapped[float] = mapped_column(Float)
    risk_free_rate: Mapped[float] = mapped_column(Float)
    volatility: Mapped[float] = mapped_column(Float)
    delta: Mapped[float] = mapped_column(Float)
    gamma: Mapped[float] = mapped_column(Float)
    theta: Mapped[float] = mapped_column(Float)
    vega: Mapped[float] = mapped_column(Float)
    rho: Mapped[float] = mapped_column(Float)
    calculated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, index=True)


class OIHistoryModel(Base):
    __tablename__ = "oi_history"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    underlying: Mapped[str] = mapped_column(String(64), index=True)
    expiry: Mapped[str] = mapped_column(String(32), index=True)
    strike_price: Mapped[float] = mapped_column(Float, index=True)
    call_oi: Mapped[int] = mapped_column(Integer, default=0)
    put_oi: Mapped[int] = mapped_column(Integer, default=0)
    total_oi: Mapped[int] = mapped_column(Integer, default=0)
    total_oi_change: Mapped[int] = mapped_column(Integer, default=0)
    total_oi_change_pct: Mapped[float] = mapped_column(Float, default=0.0)
    recorded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, index=True)


class WatchlistModel(Base):
    __tablename__ = "watchlists"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    user_id: Mapped[str] = mapped_column(String(128), index=True)
    name: Mapped[str] = mapped_column(String(128))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)


class WatchlistItemModel(Base):
    __tablename__ = "watchlist_items"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    watchlist_id: Mapped[str] = mapped_column(String(36), index=True)
    token: Mapped[str] = mapped_column(String(64), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)


class FavoriteModel(Base):
    __tablename__ = "favorites"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    user_id: Mapped[str] = mapped_column(String(128), index=True)
    token: Mapped[str] = mapped_column(String(64), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)


class NotificationPreferenceModel(Base):
    __tablename__ = "notification_preferences"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    user_id: Mapped[str] = mapped_column(String(128), index=True)
    channel: Mapped[str] = mapped_column(String(32), index=True)  # email | push
    destination: Mapped[str] = mapped_column(String(256))
    enabled: Mapped[int] = mapped_column(Integer, default=1)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)


class NotificationOutboxModel(Base):
    __tablename__ = "notification_outbox"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    user_id: Mapped[str] = mapped_column(String(128), index=True)
    channel: Mapped[str] = mapped_column(String(32), index=True)
    destination: Mapped[str] = mapped_column(String(256))
    subject: Mapped[str] = mapped_column(String(256))
    body: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(32), default="pending", index=True)  # pending/sent/failed
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class MarketplaceStrategyModel(Base):
    __tablename__ = "marketplace_strategies"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    strategy_id: Mapped[str] = mapped_column(String(36), index=True)
    owner_id: Mapped[str] = mapped_column(String(128), index=True)
    title: Mapped[str] = mapped_column(String(256))
    description: Mapped[str] = mapped_column(Text)
    tags: Mapped[list] = mapped_column(JSON)
    share_code: Mapped[str] = mapped_column(String(36), unique=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)


class UserModel(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    clerk_user_id: Mapped[str] = mapped_column(String(128), unique=True, index=True)
    email: Mapped[str | None] = mapped_column(String(256), nullable=True)
    display_name: Mapped[str | None] = mapped_column(String(128), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)


class UserPreferenceModel(Base):
    __tablename__ = "user_preferences"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    clerk_user_id: Mapped[str] = mapped_column(String(128), unique=True, index=True)
    default_timeframe: Mapped[str] = mapped_column(String(16), default="5m")
    default_indicator: Mapped[str] = mapped_column(String(32), default="rsi_14")
    theme: Mapped[str] = mapped_column(String(16), default="dark")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
