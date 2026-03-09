from __future__ import annotations

from typing import Any, Protocol


class MutableStore(Protocol):
    def create(self, table: str, payload: dict[str, Any]) -> dict[str, Any]:
        ...

    def list(self, table: str, filters: dict[str, Any] | None = None) -> list[dict[str, Any]]:
        ...
