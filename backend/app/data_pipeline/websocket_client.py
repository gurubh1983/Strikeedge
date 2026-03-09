from __future__ import annotations

import asyncio
import json
from collections.abc import Callable
from typing import Any

import websockets
from app.core.logging import get_logger, log_event

logger = get_logger("strikeedge.ws_client")


class MarketWebSocketClient:
    def __init__(
        self,
        url: str,
        on_message: Callable[[dict[str, Any]], None],
        reconnect_delay_seconds: float = 2.0,
        subscribe_payload: dict[str, Any] | None = None,
        extra_headers: dict[str, str] | None = None,
    ) -> None:
        self.url = url
        self.on_message = on_message
        self.reconnect_delay_seconds = reconnect_delay_seconds
        self.subscribe_payload = subscribe_payload
        self.extra_headers = extra_headers
        self._running = False

    async def _listen_once(self) -> None:
        async with websockets.connect(
            self.url,
            ping_interval=20,
            ping_timeout=20,
            additional_headers=self.extra_headers,
        ) as ws:
            if self.subscribe_payload is not None:
                await ws.send(json.dumps(self.subscribe_payload))
            async for raw in ws:
                try:
                    payload = json.loads(raw)
                    if isinstance(payload, dict):
                        self.on_message(payload)
                except json.JSONDecodeError:
                    continue

    async def start(self) -> None:
        self._running = True
        reconnect_count = 0
        while self._running:
            try:
                log_event(logger, "ws_connect_attempt", url=self.url, reconnect_count=reconnect_count)
                await self._listen_once()
            except Exception:
                reconnect_count += 1
                log_event(
                    logger,
                    "ws_reconnect",
                    url=self.url,
                    reconnect_count=reconnect_count,
                    delay_seconds=self.reconnect_delay_seconds,
                )
                await asyncio.sleep(self.reconnect_delay_seconds)

    def stop(self) -> None:
        self._running = False
