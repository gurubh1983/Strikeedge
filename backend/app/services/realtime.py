from __future__ import annotations

from collections import defaultdict

from fastapi import WebSocket


class RealtimeHub:
    def __init__(self) -> None:
        self.channels: dict[str, set[WebSocket]] = defaultdict(set)

    async def connect(self, channel: str, websocket: WebSocket) -> None:
        self.channels[channel].add(websocket)
        await websocket.accept()

    def disconnect(self, channel: str, websocket: WebSocket) -> None:
        self.channels[channel].discard(websocket)

    async def broadcast(self, channel: str, payload: dict) -> None:
        dead: list[WebSocket] = []
        for ws in self.channels[channel]:
            try:
                await ws.send_json(payload)
            except Exception:
                dead.append(ws)
        for ws in dead:
            self.channels[channel].discard(ws)


realtime_hub = RealtimeHub()
