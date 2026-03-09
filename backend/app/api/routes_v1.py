from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.responses import RedirectResponse

from app.core.auth import UserContext, require_user_context
from app.core.security import require_actor_id, require_idempotency_key, require_rate_limit
from app.schemas import (
    AiInsight,
    AlertIn,
    AlertOut,
    AuditEventOut,
    ChartOut,
    InstrumentOut,
    ScanRequest,
    ScanResponse,
    ScreenerIn,
    ScreenerOut,
    ScreenerUpdateIn,
    SignalOut,
    OptionsChainRowOut,
    OptionsChainMetricsOut,
    OptionsGreeksOut,
    OIHeatmapPointOut,
    CorrelationOut,
    FavoriteIn,
    FavoriteOut,
    MarketplacePublishIn,
    MarketplaceStrategyOut,
    NotificationOutboxOut,
    NotificationPreferenceIn,
    NotificationPreferenceOut,
    PatternOut,
    SentimentOut,
    StockOut,
    StrategyIn,
    StrategyOut,
    StrikeGreeksOut,
    StrikeCandleOut,
    StrikeOut,
    TickIn,
    TickIngestOut,
    WorkspaceIn,
    WorkspaceOut,
    WatchlistIn,
    WatchlistItemIn,
    WatchlistOut,
    UserPreferenceIn,
    UserPreferenceOut,
    UserProfileIn,
    UserProfileOut,
    TechnicalScanRequest,
    TechnicalScanResponse,
    TechnicalScanResultOut,
)
from app.services.ai import ai_service
from app.services.realtime import realtime_hub
from app.services.screener import screener_service
from app.services.idempotency import idempotency_service
from app.services.instruments import instrument_query_service
from app.services.market_data import market_data_service
from app.services.scan_store import scan_store_service
from app.services.screeners import screener_store_service
from app.services.signals import signal_detector
from app.services.options_chain import options_chain_service
from app.services.options_analytics import options_analytics_service
from app.services.options_volatility import options_volatility_service
from app.services.correlation import correlation_service
from app.services.notifications import notification_service
from app.services.marketplace import marketplace_service
from app.services.strategy import strategy_service
from app.services.users import user_service
from app.services.watchlists import watchlist_service
from app.services.agent_runner import agent_runner_service
from app.services.fyers_token_store import load_token
from app.core.settings import get_settings

router = APIRouter(prefix="/api/v1", tags=["v1"])


# ---------- Fyers authentication ----------
@router.get("/fyers/auth-url")
async def fyers_auth_url() -> dict:
    """Return Fyers OAuth login URL. User visits this URL, logs in, gets redirected to /callback."""
    settings = get_settings()
    app_id = settings.fyers_app_id_resolved
    secret = settings.fyers_secret_key_resolved
    redirect_uri = settings.fyers_redirect_uri_resolved
    if not app_id or not secret or not redirect_uri:
        raise HTTPException(status_code=503, detail="Fyers credentials not configured. Set STRIKEEDGE_FYERS_APP_ID, STRIKEEDGE_FYERS_SECRET_KEY, STRIKEEDGE_FYERS_REDIRECT_URI in .env")
    from app.data_pipeline.fyers_auth import FyersAuthClient
    wrapper = FyersAuthClient.build_oauth_session(app_id=app_id, secret_key=secret, redirect_uri=redirect_uri)
    url = wrapper.generate_authcode()
    return {"auth_url": url, "message": "Visit this URL in your browser to log in to Fyers."}


@router.get("/fyers/status")
async def fyers_status() -> dict:
    """Check if Fyers access token is available."""
    token = load_token()
    return {"authenticated": token is not None, "has_token": bool(token)}


@router.get("/fyers/spot/{underlying}")
async def fyers_spot(underlying: str) -> dict:
    """Get live NIFTY or BANKNIFTY spot price from Fyers."""
    from app.services.fyers_data import get_spot_price
    price = get_spot_price(underlying)
    if price is None:
        raise HTTPException(status_code=503, detail="Fyers not authenticated or symbol unavailable. Complete OAuth at GET /api/v1/fyers/auth-url")
    return {"underlying": underlying.upper(), "spot": price}


@router.get("/fyers/quotes")
async def fyers_quotes(symbols: str) -> dict:
    """Get live quotes for comma-separated symbols. E.g. symbols=NSE:NIFTY50-INDEX,NSE:BANKNIFTY-INDEX"""
    from app.services.fyers_data import get_quotes
    sym_list = [s.strip() for s in symbols.split(",") if s.strip()][:50]
    quotes = get_quotes(sym_list)
    return {"quotes": quotes}


@router.get("/fyers/expiries/{underlying}")
async def fyers_expiries(underlying: str) -> dict:
    """Get available expiry dates for an underlying (NIFTY, BANKNIFTY, etc)."""
    from app.services.fyers_data import get_expiries
    expiries = get_expiries(underlying)
    return {"underlying": underlying.upper(), "expiries": expiries}


@router.get("/fyers/history")
async def fyers_history(symbol: str, resolution: str = "5", days: int = 30) -> dict:
    """Get historical candles from Fyers. symbol e.g. NSE:NIFTY24APR24000CE, resolution: 1,5,60,D"""
    from datetime import datetime, timedelta
    from app.services.fyers_data import get_history
    to_d = datetime.now().date()
    from_d = (to_d - timedelta(days=days)).isoformat()
    to_d_str = to_d.isoformat()
    candles = get_history(symbol=symbol, resolution=resolution, from_date=from_d, to_date=to_d_str)
    return {"symbol": symbol, "candles": candles}


@router.get("/instruments", response_model=list[InstrumentOut])
async def instruments() -> list[InstrumentOut]:
    rows = instrument_query_service.list_instruments(limit=500)
    if not rows:
        rows = [{"token": "NIFTY_24000_CE"}, {"token": "NIFTY_24000_PE"}]
    return [InstrumentOut(**row) for row in rows]


@router.post("/auth/sync", response_model=UserProfileOut)
async def sync_user_profile(
    payload: UserProfileIn,
    user_ctx: UserContext = Depends(require_user_context),
) -> UserProfileOut:
    row = user_service.upsert_user(
        clerk_user_id=user_ctx.user_id,
        email=payload.email,
        display_name=payload.display_name,
    )
    return UserProfileOut(**row)


@router.get("/user", response_model=UserProfileOut)
async def get_user_profile(user_ctx: UserContext = Depends(require_user_context)) -> UserProfileOut:
    row = user_service.get_user(clerk_user_id=user_ctx.user_id)
    if row is None:
        row = user_service.upsert_user(clerk_user_id=user_ctx.user_id, email=None, display_name=None)
    return UserProfileOut(**row)


@router.get("/api/user", response_model=UserProfileOut)
async def get_user_profile_alias(user_ctx: UserContext = Depends(require_user_context)) -> UserProfileOut:
    row = user_service.get_user(clerk_user_id=user_ctx.user_id)
    if row is None:
        row = user_service.upsert_user(clerk_user_id=user_ctx.user_id, email=None, display_name=None)
    return UserProfileOut(**row)


@router.put("/user", response_model=UserProfileOut)
async def put_user_profile(
    payload: UserProfileIn,
    user_ctx: UserContext = Depends(require_user_context),
) -> UserProfileOut:
    row = user_service.upsert_user(
        clerk_user_id=user_ctx.user_id,
        email=payload.email,
        display_name=payload.display_name,
    )
    return UserProfileOut(**row)


@router.put("/api/user", response_model=UserProfileOut)
async def put_user_profile_alias(
    payload: UserProfileIn,
    user_ctx: UserContext = Depends(require_user_context),
) -> UserProfileOut:
    row = user_service.upsert_user(
        clerk_user_id=user_ctx.user_id,
        email=payload.email,
        display_name=payload.display_name,
    )
    return UserProfileOut(**row)


@router.get("/user/preferences", response_model=UserPreferenceOut)
async def get_user_preferences(user_ctx: UserContext = Depends(require_user_context)) -> UserPreferenceOut:
    row = user_service.get_preferences(clerk_user_id=user_ctx.user_id)
    if row is None:
        row = user_service.upsert_preferences(
            clerk_user_id=user_ctx.user_id,
            default_timeframe="5m",
            default_indicator="rsi_14",
            theme="dark",
        )
    return UserPreferenceOut(**row)


@router.put("/user/preferences", response_model=UserPreferenceOut)
async def put_user_preferences(
    payload: UserPreferenceIn,
    user_ctx: UserContext = Depends(require_user_context),
) -> UserPreferenceOut:
    row = user_service.upsert_preferences(
        clerk_user_id=user_ctx.user_id,
        default_timeframe=payload.default_timeframe,
        default_indicator=payload.default_indicator,
        theme=payload.theme,
    )
    return UserPreferenceOut(**row)


@router.get("/strikes/{underlying}", response_model=list[StrikeOut])
async def strikes(underlying: str) -> list[StrikeOut]:
    rows = instrument_query_service.list_strikes(underlying=underlying, limit=1200)
    if not rows:
        sym = underlying.upper()
        rows = [{"token": f"{sym}_24000_CE"}, {"token": f"{sym}_24000_PE"}]
    return [StrikeOut(**row) for row in rows]


@router.get("/strikes/{symbol}/candles", response_model=list[StrikeCandleOut])
async def strike_candles(symbol: str, timeframe: str = "1m", limit: int = 200) -> list[StrikeCandleOut]:
    from app.services.fyers_data import get_candles_for_symbol
    fyers_candles = get_candles_for_symbol(symbol=symbol, timeframe=timeframe, limit=limit)
    if fyers_candles:
        return [StrikeCandleOut(**r) for r in fyers_candles]
    resolved_token = instrument_query_service.resolve_token(symbol)
    rows = market_data_service.get_strike_candles(symbol=symbol, timeframe=timeframe, limit=limit)
    if not rows and resolved_token != symbol:
        rows = market_data_service.get_strike_candles(symbol=resolved_token, timeframe=timeframe, limit=limit)
    return [StrikeCandleOut(**row) for row in rows]


@router.post("/scan", response_model=ScanResponse)
async def scan(
    payload: ScanRequest,
    alert_user_id: str | None = None,
    _rate: None = Depends(require_rate_limit),
) -> ScanResponse:
    scan_id, results, deltas = screener_service.run_scan(payload)
    response = ScanResponse(scan_id=scan_id, created_at=datetime.now(timezone.utc), results=results)
    for delta in deltas:
        await realtime_hub.broadcast(f"scan:{scan_id}", {"type": "scan_delta", "payload": delta})
    await realtime_hub.broadcast(f"scan:{scan_id}", {"type": "scan_result", "payload": response.model_dump(mode="json")})
    if alert_user_id:
        matched_tokens = [row.token for row in results if row.matched]
        if matched_tokens:
            notification_service.queue_alert_notification(
                user_id=alert_user_id,
                subject=f"Scan matched {len(matched_tokens)} instruments",
                body=f"Matched tokens: {', '.join(matched_tokens[:20])}",
            )
            await realtime_hub.broadcast(
                f"alerts:{alert_user_id}",
                {
                    "type": "scan_match_alert",
                    "payload": {"scan_id": scan_id, "matched_count": len(matched_tokens), "tokens": matched_tokens[:20]},
                },
            )
    return response


@router.post("/scanner/technical", response_model=TechnicalScanResponse)
async def technical_scanner(payload: TechnicalScanRequest) -> TechnicalScanResponse:
    """
    Scan option strikes by technical indicators on strike price charts.
    Fetches candles for each strike, computes RSI, MACD, EMA, filters by rules.
    """
    from app.services.technical_scanner import scan_strikes
    rules_dict = [{"indicator": r.indicator, "operator": r.operator, "value": r.value} for r in payload.rules]
    if not rules_dict and not (payload.filter_config and payload.filter_config.get("groups")):
        return TechnicalScanResponse(results=[], count=0)
    results = scan_strikes(
        underlyings=payload.underlyings,
        expiry=payload.expiry,
        rules=rules_dict,
        timeframe=payload.timeframe,
        candle_days=payload.candle_days,
        max_strikes_per_underlying=payload.max_strikes_per_underlying,
        filter_config=payload.filter_config,
    )
    out = [TechnicalScanResultOut(**r) for r in results]
    return TechnicalScanResponse(results=out, count=len(out))


@router.get("/scan/{scan_id}/results")
async def scan_results(scan_id: str) -> dict:
    row = scan_store_service.get_scan(scan_id)
    if row is None:
        return {"scan_id": scan_id, "status": "not_found", "results": []}
    return row


@router.post("/screeners", response_model=ScreenerOut)
async def create_screener(payload: ScreenerIn) -> ScreenerOut:
    created = screener_store_service.create(payload)
    return ScreenerOut(**created)


@router.get("/screeners", response_model=list[ScreenerOut])
async def list_screeners(user_id: str | None = None) -> list[ScreenerOut]:
    rows = screener_store_service.list(user_id=user_id)
    return [ScreenerOut(**row) for row in rows]


@router.get("/screeners/{screener_id}", response_model=ScreenerOut)
async def get_screener(screener_id: str) -> ScreenerOut:
    row = screener_store_service.get(screener_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Screener not found")
    return ScreenerOut(**row)


@router.put("/screeners/{screener_id}", response_model=ScreenerOut)
async def update_screener(screener_id: str, payload: ScreenerUpdateIn) -> ScreenerOut:
    row = screener_store_service.update(screener_id, payload)
    if row is None:
        raise HTTPException(status_code=404, detail="Screener not found")
    return ScreenerOut(**row)


@router.delete("/screeners/{screener_id}")
async def delete_screener(screener_id: str) -> dict[str, bool]:
    deleted = screener_store_service.delete(screener_id)
    return {"deleted": deleted}


@router.get("/chart/{strike_token}", response_model=ChartOut)
async def chart(strike_token: str, timeframe: str = "5m", limit: int = 200) -> ChartOut:
    from app.services.fyers_data import get_candles_for_symbol
    fyers_candles = get_candles_for_symbol(symbol=strike_token, timeframe=timeframe, limit=limit)
    if fyers_candles:
        return ChartOut(token=strike_token, timeframe=timeframe, candles=fyers_candles)
    candles = market_data_service.get_chart(token=strike_token, timeframe=timeframe, limit=limit)
    return ChartOut(token=strike_token, timeframe=timeframe, candles=candles)


@router.post("/internal/ticks", response_model=TickIngestOut)
async def ingest_tick(
    payload: TickIn,
    _rate: None = Depends(require_rate_limit),
) -> TickIngestOut:
    result = market_data_service.ingest_tick(
        token=payload.token,
        ltp=payload.ltp,
        volume=payload.volume,
        timeframe=payload.timeframe,
        ts=payload.ts,
    )
    return TickIngestOut(**result)


@router.get("/internal/indicators/{token}")
async def latest_indicator(token: str, timeframe: str = "1m") -> dict:
    row = market_data_service.latest_indicator_for_token(token=token, timeframe=timeframe)
    return {"token": token, "timeframe": timeframe, "indicator": row}


@router.post("/strategies", response_model=StrategyOut)
async def create_strategy(
    payload: StrategyIn,
    _actor: str = Depends(require_actor_id),
    idem_key: str = Depends(require_idempotency_key),
    _rate: None = Depends(require_rate_limit),
    user_ctx: UserContext = Depends(require_user_context),
) -> StrategyOut:
    endpoint = "POST:/api/v1/strategies"
    cached = idempotency_service.fetch(user_ctx.user_id, idem_key, endpoint)
    if cached is not None:
        return StrategyOut(**cached)
    created = strategy_service.create_strategy(payload, actor_id=user_ctx.user_id)
    idempotency_service.store(user_ctx.user_id, idem_key, endpoint, created)
    return StrategyOut(**created)


@router.post("/workspaces", response_model=WorkspaceOut)
async def create_workspace(
    payload: WorkspaceIn,
    _actor: str = Depends(require_actor_id),
    idem_key: str = Depends(require_idempotency_key),
    _rate: None = Depends(require_rate_limit),
    user_ctx: UserContext = Depends(require_user_context),
) -> WorkspaceOut:
    endpoint = "POST:/api/v1/workspaces"
    cached = idempotency_service.fetch(user_ctx.user_id, idem_key, endpoint)
    if cached is not None:
        return WorkspaceOut(**cached)
    created = strategy_service.create_workspace(payload, actor_id=user_ctx.user_id)
    idempotency_service.store(user_ctx.user_id, idem_key, endpoint, created)
    return WorkspaceOut(**created)


@router.post("/alerts", response_model=AlertOut)
async def create_alert(
    payload: AlertIn,
    _actor: str = Depends(require_actor_id),
    idem_key: str = Depends(require_idempotency_key),
    _rate: None = Depends(require_rate_limit),
    user_ctx: UserContext = Depends(require_user_context),
) -> AlertOut:
    endpoint = "POST:/api/v1/alerts"
    cached = idempotency_service.fetch(user_ctx.user_id, idem_key, endpoint)
    if cached is not None:
        return AlertOut(**cached)
    alert = strategy_service.create_alert(payload, actor_id=user_ctx.user_id)
    idempotency_service.store(user_ctx.user_id, idem_key, endpoint, alert)
    notification_service.queue_alert_notification(
        user_id=payload.user_id,
        subject=f"Alert created: {payload.name}",
        body=f"Alert {payload.name} was created for rule {payload.rule.field} {payload.rule.operator} {payload.rule.value}",
    )
    await realtime_hub.broadcast(f"alerts:{payload.user_id}", {"type": "alert_created", "payload": alert})
    return AlertOut(**alert)


@router.get("/alerts", response_model=list[AlertOut])
async def list_alerts(
    user_id: str | None = None,
    limit: int = 50,
    offset: int = 0,
    sort_by: str = "created_at",
    sort_order: str = "desc",
) -> list[AlertOut]:
    return strategy_service.list_alerts(
        user_id=user_id,
        limit=limit,
        offset=offset,
        sort_by=sort_by,
        sort_order=sort_order,
    )


@router.get("/alerts/cursor")
async def list_alerts_cursor(
    user_id: str | None = None,
    limit: int = 50,
    cursor: str | None = None,
    sort_by: str = "created_at",
    sort_order: str = "desc",
) -> dict:
    return strategy_service.list_alerts_cursor(
        user_id=user_id,
        limit=limit,
        cursor=cursor,
        sort_by=sort_by,
        sort_order=sort_order,
    )


@router.get("/audit/events", response_model=list[AuditEventOut])
async def list_audit_events(
    actor_id: str | None = None,
    entity_type: str | None = None,
    limit: int = 100,
    offset: int = 0,
    sort_by: str = "created_at",
    sort_order: str = "desc",
) -> list[AuditEventOut]:
    return strategy_service.list_audit(
        actor_id=actor_id,
        entity_type=entity_type,
        limit=limit,
        offset=offset,
        sort_by=sort_by,
        sort_order=sort_order,
    )


@router.get("/audit/events/cursor")
async def list_audit_events_cursor(
    actor_id: str | None = None,
    entity_type: str | None = None,
    limit: int = 100,
    cursor: str | None = None,
    sort_by: str = "created_at",
    sort_order: str = "desc",
) -> dict:
    return strategy_service.list_audit_cursor(
        actor_id=actor_id,
        entity_type=entity_type,
        limit=limit,
        cursor=cursor,
        sort_by=sort_by,
        sort_order=sort_order,
    )


@router.get("/stock/{symbol}", response_model=StockOut)
async def stock_detail(symbol: str) -> StockOut:
    return StockOut(symbol=symbol.upper(), price=2450.25, change_percent=1.42)


@router.get("/ai/insights/{symbol}", response_model=AiInsight)
async def ai_insights(symbol: str) -> AiInsight:
    return ai_service.generate(symbol)


@router.get("/ai/sentiment/{symbol}", response_model=SentimentOut)
async def ai_sentiment(symbol: str) -> SentimentOut:
    return ai_service.sentiment(symbol)


@router.get("/ai/patterns/{symbol}", response_model=PatternOut)
async def ai_patterns(symbol: str, timeframe: str = "5m") -> PatternOut:
    return ai_service.detect_patterns(symbol, timeframe=timeframe)


@router.get("/signals", response_model=list[SignalOut])
async def list_signals(token: str | None = None, limit: int = 100) -> list[SignalOut]:
    rows = signal_detector.list_events(token=token, limit=limit)
    return [SignalOut(**row) for row in rows]


@router.get("/options/chain", response_model=list[OptionsChainRowOut])
async def get_options_chain(
    underlying: str,
    expiry: str,
    limit: int = 200,
    refresh: bool = False,
) -> list[OptionsChainRowOut]:
    if refresh:
        await options_chain_service.refresh_chain(underlying=underlying, expiry=expiry)
    rows = options_chain_service.get_chain(underlying=underlying, expiry=expiry, limit=limit)
    return [OptionsChainRowOut(**row) for row in rows]


@router.get("/options/metrics", response_model=OptionsChainMetricsOut)
async def get_options_chain_metrics(underlying: str, expiry: str) -> OptionsChainMetricsOut:
    row = options_chain_service.get_chain_metrics(underlying=underlying, expiry=expiry)
    return OptionsChainMetricsOut(**row)


@router.get("/options/greeks", response_model=OptionsGreeksOut)
async def get_options_greeks(
    option_type: str,
    spot: float,
    strike: float,
    time_to_expiry_years: float,
    risk_free_rate: float = 0.06,
    volatility: float = 0.2,
) -> OptionsGreeksOut:
    values = options_analytics_service.greeks(
        option_type=option_type,
        spot=spot,
        strike=strike,
        time_to_expiry_years=time_to_expiry_years,
        risk_free_rate=risk_free_rate,
        volatility=volatility,
    )
    return OptionsGreeksOut(
        option_type=option_type.upper(),
        spot=spot,
        strike=strike,
        time_to_expiry_years=time_to_expiry_years,
        risk_free_rate=risk_free_rate,
        volatility=volatility,
        **values,
    )


@router.post("/options/greeks/calculate")
async def calculate_chain_greeks(
    underlying: str,
    expiry: str,
    spot: float,
    time_to_expiry_years: float,
    risk_free_rate: float = 0.06,
) -> dict[str, int]:
    rows = options_volatility_service.calculate_greeks_for_chain(
        underlying=underlying,
        expiry=expiry,
        spot=spot,
        time_to_expiry_years=time_to_expiry_years,
        risk_free_rate=risk_free_rate,
    )
    return {"calculated": rows}


@router.get("/strikes/{symbol}/vol/greeks", response_model=StrikeGreeksOut)
async def get_strike_symbol_greeks(symbol: str) -> StrikeGreeksOut:
    row = options_volatility_service.get_symbol_greeks(symbol=symbol)
    if row is None:
        raise HTTPException(status_code=404, detail="Strike greeks not found")
    return StrikeGreeksOut(**row)


@router.get("/options/oi/heatmap", response_model=list[OIHeatmapPointOut])
async def get_oi_heatmap(underlying: str, expiry: str, limit: int = 200) -> list[OIHeatmapPointOut]:
    rows = options_volatility_service.oi_heatmap(underlying=underlying, expiry=expiry, limit=limit)
    return [OIHeatmapPointOut(**row) for row in rows]


@router.get("/options/oi/spikes", response_model=list[OIHeatmapPointOut])
async def get_oi_spikes(
    underlying: str,
    expiry: str,
    threshold_pct: float = 20.0,
    limit: int = 100,
) -> list[OIHeatmapPointOut]:
    rows = options_volatility_service.oi_spikes(
        underlying=underlying,
        expiry=expiry,
        threshold_pct=threshold_pct,
        limit=limit,
    )
    return [OIHeatmapPointOut(**row) for row in rows]


@router.get("/options/correlation", response_model=CorrelationOut)
async def get_options_correlation(
    token_a: str,
    token_b: str,
    timeframe: str = "5m",
    limit: int = 200,
) -> CorrelationOut:
    row = correlation_service.price_correlation(token_a=token_a, token_b=token_b, timeframe=timeframe, limit=limit)
    return CorrelationOut(**row)


@router.post("/watchlists", response_model=WatchlistOut)
async def create_watchlist(payload: WatchlistIn) -> WatchlistOut:
    row = watchlist_service.create_watchlist(user_id=payload.user_id, name=payload.name)
    await realtime_hub.broadcast(f"watchlists:{payload.user_id}", {"type": "watchlist_created", "payload": row})
    return WatchlistOut(**row)


@router.get("/watchlists", response_model=list[WatchlistOut])
async def list_watchlists(user_id: str) -> list[WatchlistOut]:
    rows = watchlist_service.list_watchlists(user_id=user_id)
    return [WatchlistOut(**row) for row in rows]


@router.post("/watchlists/{watchlist_id}/items", response_model=WatchlistOut)
async def add_watchlist_item(watchlist_id: str, payload: WatchlistItemIn) -> WatchlistOut:
    row = watchlist_service.add_watchlist_item(watchlist_id=watchlist_id, token=payload.token)
    if row is None:
        raise HTTPException(status_code=404, detail="Watchlist not found")
    await realtime_hub.broadcast(f"watchlists:{row['user_id']}", {"type": "watchlist_updated", "payload": row})
    return WatchlistOut(**row)


@router.post("/favorites", response_model=FavoriteOut)
async def create_favorite(payload: FavoriteIn) -> FavoriteOut:
    row = watchlist_service.create_favorite(user_id=payload.user_id, token=payload.token)
    return FavoriteOut(**row)


@router.get("/favorites", response_model=list[FavoriteOut])
async def list_favorites(user_id: str) -> list[FavoriteOut]:
    rows = watchlist_service.list_favorites(user_id=user_id)
    return [FavoriteOut(**row) for row in rows]


@router.delete("/favorites")
async def delete_favorite(user_id: str, token: str) -> dict[str, bool]:
    deleted = watchlist_service.delete_favorite(user_id=user_id, token=token)
    return {"deleted": deleted}


@router.post("/notifications/preferences", response_model=NotificationPreferenceOut)
async def upsert_notification_preference(payload: NotificationPreferenceIn) -> NotificationPreferenceOut:
    row = notification_service.upsert_preference(
        user_id=payload.user_id,
        channel=payload.channel,
        destination=payload.destination,
        enabled=payload.enabled,
    )
    return NotificationPreferenceOut(**row)


@router.get("/notifications/preferences", response_model=list[NotificationPreferenceOut])
async def list_notification_preferences(user_id: str) -> list[NotificationPreferenceOut]:
    rows = notification_service.list_preferences(user_id=user_id)
    return [NotificationPreferenceOut(**row) for row in rows]


@router.get("/notifications/outbox", response_model=list[NotificationOutboxOut])
async def list_notification_outbox(user_id: str, limit: int = 100) -> list[NotificationOutboxOut]:
    rows = notification_service.list_outbox(user_id=user_id, limit=limit)
    return [NotificationOutboxOut(**row) for row in rows]


@router.post("/notifications/outbox/{outbox_id}/dispatch", response_model=NotificationOutboxOut)
async def dispatch_notification(outbox_id: str) -> NotificationOutboxOut:
    row = notification_service.dispatch_outbox_item(outbox_id=outbox_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Outbox item not found")
    return NotificationOutboxOut(**row)


@router.post("/notifications/outbox/dispatch/pending")
async def dispatch_pending_notifications(limit: int = 100) -> dict[str, int]:
    return notification_service.dispatch_pending(limit=limit)


@router.post("/marketplace/publish", response_model=MarketplaceStrategyOut)
async def publish_marketplace_strategy(payload: MarketplacePublishIn) -> MarketplaceStrategyOut:
    row = marketplace_service.publish_strategy(
        strategy_id=payload.strategy_id,
        owner_id=payload.owner_id,
        title=payload.title,
        description=payload.description,
        tags=payload.tags,
    )
    return MarketplaceStrategyOut(**row)


@router.get("/marketplace/strategies", response_model=list[MarketplaceStrategyOut])
async def list_marketplace_strategies(limit: int = 100) -> list[MarketplaceStrategyOut]:
    rows = marketplace_service.list_marketplace(limit=limit)
    return [MarketplaceStrategyOut(**row) for row in rows]


@router.get("/marketplace/share/{share_code}", response_model=MarketplaceStrategyOut)
async def get_marketplace_share(share_code: str) -> MarketplaceStrategyOut:
    row = marketplace_service.get_by_share_code(share_code=share_code)
    if row is None:
        raise HTTPException(status_code=404, detail="Strategy share not found")
    return MarketplaceStrategyOut(**row)


@router.post("/agents/jobs")
async def create_agent_job(
    payload: dict,
    user_ctx: UserContext = Depends(require_user_context),
) -> dict:
    job_type = str(payload.get("job_type") or "SCAN")
    request_payload = dict(payload.get("request_payload") or payload)
    request_payload.setdefault("workflow", job_type)
    created = agent_runner_service.create_job(
        user_id=user_ctx.user_id,
        job_type=job_type,
        request_payload=request_payload,
    )
    return created


@router.post("/agents/jobs/{job_id}/run")
async def run_agent_job(job_id: str) -> dict:
    result = await agent_runner_service.run_job(job_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Job not found")
    return result


@router.get("/agents/jobs/{job_id}")
async def get_agent_job(job_id: str) -> dict:
    row = agent_runner_service.get_job(job_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Job not found")
    return row


@router.websocket("/ws/scan/{scan_id}")
async def ws_scan(websocket: WebSocket, scan_id: str) -> None:
    channel = f"scan:{scan_id}"
    await realtime_hub.connect(channel, websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        realtime_hub.disconnect(channel, websocket)


@router.websocket("/ws/alerts/{user_id}")
async def ws_alerts(websocket: WebSocket, user_id: str) -> None:
    channel = f"alerts:{user_id}"
    await realtime_hub.connect(channel, websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        realtime_hub.disconnect(channel, websocket)


@router.websocket("/ws/watchlists/{user_id}")
async def ws_watchlists(websocket: WebSocket, user_id: str) -> None:
    channel = f"watchlists:{user_id}"
    await realtime_hub.connect(channel, websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        realtime_hub.disconnect(channel, websocket)
