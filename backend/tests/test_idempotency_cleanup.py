from __future__ import annotations

from app.services.idempotency import IdempotencyService


def test_idempotency_cleanup_memory() -> None:
    service = IdempotencyService()
    service.store("u1", "k1", "POST:/x", {"id": "1"})
    key = ("u1", "k1", "POST:/x")
    service._memory[key]["_created_at"] = 0  # force-expired for cleanup path
    cleaned = service.cleanup_expired()
    assert cleaned >= 1
    assert service.fetch("u1", "k1", "POST:/x") is None
