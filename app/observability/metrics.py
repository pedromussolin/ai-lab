"""Basic metrics collection (can be extended with Prometheus)."""

from collections import defaultdict
from typing import Any


class MetricsCollector:
    """Simple in-memory metrics collector."""

    def __init__(self) -> None:
        self._counters: dict[str, int] = defaultdict(int)
        self._histograms: dict[str, list[float]] = defaultdict(list)

    def increment(self, metric: str, value: int = 1, **labels: Any) -> None:
        key = self._key(metric, labels)
        self._counters[key] += value

    def record(self, metric: str, value: float, **labels: Any) -> None:
        key = self._key(metric, labels)
        self._histograms[key].append(value)

    def get_counter(self, metric: str, **labels: Any) -> int:
        return self._counters[self._key(metric, labels)]

    def get_summary(self) -> dict[str, Any]:
        return {
            "counters": dict(self._counters),
            "histogram_counts": {k: len(v) for k, v in self._histograms.items()},
        }

    @staticmethod
    def _key(metric: str, labels: dict) -> str:
        if labels:
            label_str = ",".join(f"{k}={v}" for k, v in sorted(labels.items()))
            return f"{metric}{{{label_str}}}"
        return metric


metrics = MetricsCollector()
