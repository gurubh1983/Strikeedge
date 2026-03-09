from __future__ import annotations

from collections import defaultdict
from typing import Any


class InMemoryStore:
    def __init__(self) -> None:
        self._tables: dict[str, list[dict[str, Any]]] = defaultdict(list)

    def create(self, table: str, payload: dict[str, Any]) -> dict[str, Any]:
        self._tables[table].append(payload)
        return payload

    def list(self, table: str, filters: dict[str, Any] | None = None) -> list[dict[str, Any]]:
        rows = list(self._tables[table])
        if not filters:
            return rows
        out: list[dict[str, Any]] = []
        for row in rows:
            matched = True
            for key, value in filters.items():
                if value is None:
                    continue
                if row.get(key) != value:
                    matched = False
                    break
            if matched:
                out.append(row)
        return out
