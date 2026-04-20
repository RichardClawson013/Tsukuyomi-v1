"""Prometheus-style metrics. Optional; enabled via config."""
from __future__ import annotations
from typing import Any

# Minimal metrics shim — uses prometheus_client if available, else no-op.
try:
    from prometheus_client import Counter, Gauge, Histogram, generate_latest, CONTENT_TYPE_LATEST
    _PROM_AVAILABLE = True
except ImportError:  # pragma: no cover
    _PROM_AVAILABLE = False
    Counter = Gauge = Histogram = None
    generate_latest = lambda: b""  # type: ignore
    CONTENT_TYPE_LATEST = "text/plain"


class Metrics:
    def __init__(self) -> None:
        if not _PROM_AVAILABLE:
            self.requests_total = self.organ_decisions_total = self.knee_blocks_total = None
            self.gary_audits_total = self.budget_zone = None
            self.organ_latency_ms = None
            return
        self.requests_total = Counter("tsukuyomi_requests_total", "Total requests", ["tier", "decision"])
        self.organ_decisions_total = Counter("tsukuyomi_organ_decisions_total", "Per-organ decisions", ["organ", "decision"])
        self.knee_blocks_total = Counter("tsukuyomi_knee_blocks_total", "Knee blocks", ["pattern_id"])
        self.gary_audits_total = Counter("tsukuyomi_gary_audits_total", "Gary audits", ["result"])
        self.budget_zone = Gauge("tsukuyomi_budget_zone", "Current budget zone", ["zone"])
        self.organ_latency_ms = Histogram("tsukuyomi_organ_latency_ms", "Per-organ latency", ["organ"])

    def export(self) -> tuple[bytes, str]:
        return generate_latest(), CONTENT_TYPE_LATEST


METRICS = Metrics()
