from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.exceptions import HTTPException as FastAPIHTTPException
from fastapi.responses import PlainTextResponse, RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from app.api.routes_v1 import router as v1_router
from app.core.errors import http_exception_handler, unhandled_exception_handler
from app.core.metrics import metrics_registry
from app.core.observability import TraceMiddleware
from app.core.settings import get_settings
from app.core.startup_checks import validate_runtime_settings
from app.db.session import get_session_factory, init_db
from app.repositories.sqlalchemy import SqlAlchemyStore
from app.services.idempotency import idempotency_service
from app.services.instruments import instrument_query_service
from app.services.market_data import market_data_service
from app.services.scan_store import scan_store_service
from app.services.screeners import screener_store_service
from app.services.signals import signal_detector
from app.services.options_chain import options_chain_service
from app.services.options_volatility import options_volatility_service
from app.services.correlation import correlation_service
from app.services.notifications import notification_service
from app.services.marketplace import marketplace_service
from app.services.strategy import strategy_service
from app.services.users import user_service
from app.services.watchlists import watchlist_service
from app.services.agent_runner import agent_runner_service
from app.services.agent_scheduler import create_scheduler
from app.services.fyers_token_store import save_token


def create_app() -> FastAPI:
    settings = get_settings()
    
    @asynccontextmanager
    async def lifespan(_app: FastAPI):
        validate_runtime_settings(settings)
        init_db(settings)
        session_factory = get_session_factory(settings)
        _app.state.session_factory = session_factory
        strategy_service.set_store(SqlAlchemyStore(session_factory))
        idempotency_service.set_session_factory(session_factory)
        instrument_query_service.set_session_factory(session_factory)
        market_data_service.set_session_factory(session_factory)
        scan_store_service.set_session_factory(session_factory)
        screener_store_service.set_session_factory(session_factory)
        signal_detector.set_session_factory(session_factory)
        options_chain_service.set_session_factory(session_factory)
        options_volatility_service.set_session_factory(session_factory)
        correlation_service.set_session_factory(session_factory)
        watchlist_service.set_session_factory(session_factory)
        notification_service.set_session_factory(session_factory)
        marketplace_service.set_session_factory(session_factory)
        user_service.set_session_factory(session_factory)
        agent_runner_service.set_session_factory(session_factory)
        scheduler = None
        try:
            scheduler = create_scheduler(agent_runner_service)
            scheduler.start()
        except Exception:
            pass
        yield
        if scheduler:
            try:
                scheduler.shutdown(wait=False)
            except Exception:
                pass

    app = FastAPI(title=settings.app_name, version=settings.app_version, lifespan=lifespan)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.add_middleware(TraceMiddleware)
    # Dashboard routes (before v1 router to avoid path conflicts)
    @app.get("/dashboard-overview")
    async def dashboard_market_overview_root() -> dict:
        from app.services.dashboard_service import get_market_overview
        return get_market_overview()

    @app.get("/api/v1/dashboard/market-overview")
    async def dashboard_market_overview() -> dict:
        from app.services.dashboard_service import get_market_overview
        return get_market_overview()

    app.include_router(v1_router)
    app.add_exception_handler(FastAPIHTTPException, http_exception_handler)
    app.add_exception_handler(Exception, unhandled_exception_handler)

    @app.get("/callback")
    async def fyers_oauth_callback(auth_code: str | None = None):
        """Fyers OAuth callback. Exchanges auth_code for access_token and stores it."""
        if not auth_code or not auth_code.strip():
            raise HTTPException(status_code=400, detail="Missing auth_code. Login failed.")
        settings = get_settings()
        app_id = settings.fyers_app_id_resolved
        secret = settings.fyers_secret_key_resolved
        redirect_uri = settings.fyers_redirect_uri_resolved
        if not app_id or not secret:
            raise HTTPException(status_code=503, detail="Fyers credentials not configured")
        try:
            from app.data_pipeline.fyers_auth import FyersAuthClient
            session = await FyersAuthClient.exchange_auth_code(
                app_id=app_id,
                secret_key=secret,
                redirect_uri=redirect_uri,
                auth_code=auth_code.strip(),
            )
            save_token(session.access_token, session.refresh_token)
            import os
            frontend_url = os.environ.get("FRONTEND_URL", "http://localhost:3000")
            return RedirectResponse(url=f"{frontend_url}/?fyers_auth=success")
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))

    @app.get("/health")
    async def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.get("/ready")
    async def ready() -> dict[str, str]:
        session_factory = getattr(app.state, "session_factory", None)
        if session_factory is None:
            return {"status": "initializing"}
        with session_factory() as session:
            session.execute(text("SELECT 1"))
        return {"status": "ready"}

    @app.get("/metrics")
    async def metrics() -> dict[str, int]:
        return metrics_registry.snapshot()

    @app.get("/metrics/prometheus", response_class=PlainTextResponse)
    async def metrics_prometheus() -> str:
        return metrics_registry.render_prometheus()

    return app


app = create_app()
