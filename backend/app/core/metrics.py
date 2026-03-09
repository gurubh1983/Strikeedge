from __future__ import annotations

from collections import defaultdict
from threading import Lock


class MetricsRegistry:
    def __init__(self) -> None:
        self._counters: dict[str, int] = defaultdict(int)
        self._lock = Lock()

    def incr(self, name: str, amount: int = 1) -> None:
        with self._lock:
            self._counters[name] += amount

    def snapshot(self) -> dict[str, int]:
        with self._lock:
            return dict(self._counters)

    def render_prometheus(self) -> str:
        with self._lock:
            lines: list[str] = []
            for key in sorted(self._counters.keys()):
                metric_name = key.replace(".", "_").replace("-", "_")
                lines.append(f"# TYPE {metric_name} counter")
                lines.append(f"{metric_name} {self._counters[key]}")
            return "\n".join(lines) + ("\n" if lines else "")


metrics_registry = MetricsRegistry()
