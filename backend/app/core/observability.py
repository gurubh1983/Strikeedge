from __future__ import annotations

from time import perf_counter
from uuid import uuid4

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.logging import get_logger, log_event
from app.core.metrics import metrics_registry

logger = get_logger("strikeedge.http")


class TraceMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        trace_id = request.headers.get("x-trace-id", str(uuid4()))
        request.state.trace_id = trace_id
        started = perf_counter()
        response = await call_next(request)
        elapsed_ms = (perf_counter() - started) * 1000
        response.headers["x-trace-id"] = trace_id
        response.headers["x-elapsed-ms"] = f"{elapsed_ms:.2f}"

        metrics_registry.incr("http_requests_total")
        metrics_registry.incr(f"http_status_{response.status_code}")
        log_event(
            logger,
            "http_request",
            trace_id=trace_id,
            method=request.method,
            path=request.url.path,
            status_code=response.status_code,
            elapsed_ms=round(elapsed_ms, 2),
        )
        return response
