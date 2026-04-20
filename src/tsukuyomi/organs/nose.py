"""Nose — anomaly and loop detection.

Spec: docs/architecture/03_organs.md §4.7.
"""
from __future__ import annotations
import hashlib
import time
from collections import deque
from dataclasses import dataclass
from typing import Any, Literal

from tsukuyomi.core.nervecore import NerveCoreInterface, Signal
from tsukuyomi.observability.logging import get_logger

log = get_logger(__name__)


@dataclass
class AnomalySignal:
    severity: Literal["info", "warn", "error", "critical"]
    metric: str
    value: float | int
    threshold: float | int


class Nose:
    def __init__(self, config: Any, nerve: NerveCoreInterface) -> None:
        self.config = config
        self.nerve = nerve
        self._recent_commands: deque[tuple[float, str]] = deque(maxlen=64)
        self._recent_errors: deque[float] = deque(maxlen=64)
        self._recent_tokens: deque[tuple[float, int]] = deque(maxlen=128)
        self._recent_tool_calls: deque[float] = deque(maxlen=128)

    async def observe_command(self, command: str) -> list[AnomalySignal]:
        now = time.time()
        h = hashlib.sha256(command.encode()).hexdigest()[:16]
        self._recent_commands.append((now, h))
        signals = []

        window = int(getattr(self.config, "window_seconds", 60))
        threshold = int(getattr(self.config, "max_identical_commands", 3))
        same = sum(1 for t, hh in self._recent_commands if hh == h and (now - t) <= window)
        if same >= threshold:
            sig = AnomalySignal(severity="critical", metric="identical_command_loop",
                                value=same, threshold=threshold)
            signals.append(sig)
            log.error("nose.loop_detected", command_hash=h, count=same)
            await self.nerve.publish(Signal(topic="nose.loop",
                                             payload={"hash": h, "count": same}))
        return signals

    async def observe_tokens(self, count: int) -> list[AnomalySignal]:
        now = time.time()
        self._recent_tokens.append((now, count))
        window = 60
        cutoff = now - window
        rate = sum(c for t, c in self._recent_tokens if t >= cutoff)
        max_rate = int(getattr(self.config, "max_token_rate_per_min", 500))
        signals = []
        if rate > max_rate:
            signals.append(AnomalySignal(severity="warn", metric="token_rate",
                                          value=rate, threshold=max_rate))
            log.warning("nose.token_rate_high", rate_per_min=rate, threshold=max_rate)
        return signals

    async def observe_error(self) -> list[AnomalySignal]:
        now = time.time()
        self._recent_errors.append(now)
        cutoff = now - 120
        recent = sum(1 for t in self._recent_errors if t >= cutoff)
        threshold = int(getattr(self.config, "max_errors_per_2min", 5))
        signals = []
        if recent > threshold:
            signals.append(AnomalySignal(severity="error", metric="error_rate",
                                          value=recent, threshold=threshold))
            await self.nerve.publish(Signal(topic="nose.error_burst",
                                             payload={"count": recent}))
        return signals
