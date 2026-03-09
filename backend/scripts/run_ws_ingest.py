from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from typing import Any

from app.core.settings import get_settings
from app.data_pipeline.fyers_auth import FyersAuthClient
from app.data_pipeline.websocket_client import MarketWebSocketClient
from app.db.session import get_session_factory, init_db
from app.services.market_data import market_data_service


def _on_message(payload: dict[str, Any]) -> None:
    token = str(payload.get("token", "")).strip()
    ltp = payload.get("ltp")
    if not token or ltp is None:
        return
    volume = int(payload.get("volume", 0) or 0)
    timeframe = str(payload.get("timeframe", "1m"))
    ts_raw = payload.get("ts")
    ts = None
    if isinstance(ts_raw, str):
        try:
            ts = datetime.fromisoformat(ts_raw.replace("Z", "+00:00"))
        except ValueError:
            ts = datetime.now(timezone.utc)
    market_data_service.ingest_tick(token=token, ltp=float(ltp), volume=volume, timeframe=timeframe, ts=ts)


async def main() -> None:
    settings = get_settings()
    init_db(settings)
    session_factory = get_session_factory(settings)
    market_data_service.set_session_factory(session_factory)

    ws_url = "ws://127.0.0.1:8765"
    ws_headers: dict[str, str] | None = None
    app_id = settings.fyers_app_id_resolved
    secret = settings.fyers_secret_key_resolved
    redirect_uri = settings.fyers_redirect_uri_resolved
    totp = settings.fyers_totp_secret_resolved
    if app_id and secret and redirect_uri and totp:
        auth_client = FyersAuthClient(base_url=settings.fyers_rest_base_url)
        session = await auth_client.create_session(
            app_id=app_id,
            secret_key=secret,
            redirect_uri=redirect_uri,
            totp_secret=totp,
        )
        ws_headers = auth_client.build_ws_headers(
            session=session,
            app_id=app_id,
        )
        ws_url = settings.fyers_ws_base_url
    subscribe_payload = {
        "type": "subscribe",
        "symbols": ["NSE:NIFTY24APR24000CE", "NSE:NIFTY24APR24000PE"],
        "data_type": "symbolData",
    }
    client = MarketWebSocketClient(
        url=ws_url,
        on_message=_on_message,
        reconnect_delay_seconds=2.0,
        subscribe_payload=subscribe_payload,
        extra_headers=ws_headers,
    )
    await client.start()


if __name__ == "__main__":
    asyncio.run(main())
