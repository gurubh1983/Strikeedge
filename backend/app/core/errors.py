from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from fastapi import Request
from fastapi.responses import JSONResponse


def error_envelope(
    *,
    code: str,
    message: str,
    status_code: int,
    trace_id: str | None = None,
    details: dict[str, Any] | None = None,
) -> JSONResponse:
    payload = {
        "error": {
            "code": code,
            "message": message,
            "trace_id": trace_id,
            "details": details or {},
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
    }
    return JSONResponse(status_code=status_code, content=payload)


def http_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    trace_id = getattr(request.state, "trace_id", None)
    status_code = getattr(exc, "status_code", 500)
    detail = getattr(exc, "detail", "Internal server error")
    code = "http_error" if status_code < 500 else "internal_error"
    return error_envelope(
        code=code,
        message=str(detail),
        status_code=status_code,
        trace_id=trace_id,
    )


def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    trace_id = getattr(request.state, "trace_id", None)
    return error_envelope(
        code="internal_error",
        message="Unexpected server error",
        status_code=500,
        trace_id=trace_id,
        details={"exception_type": exc.__class__.__name__},
    )
