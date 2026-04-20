"""NerveCore — the in-process pub/sub bus.

ADR 0006: asyncio.Queue based for v1.0; the interface allows a ZeroMQ-backed
implementation in v1.2 without organ-side changes.
"""
from __future__ import annotations
import asyncio
from dataclasses import dataclass, field
from typing import Any, Awaitable, Callable, Protocol


@dataclass
class Signal:
    topic: str
    payload: dict[str, Any] = field(default_factory=dict)


SignalHandler = Callable[[Signal], Awaitable[None]]


class NerveCoreInterface(Protocol):
    async def publish(self, signal: Signal) -> None: ...
    def subscribe(self, topic_pattern: str, handler: SignalHandler) -> None: ...
    async def shutdown(self) -> None: ...


class AsyncioNerveCore:
    """Default in-process bus."""

    def __init__(self) -> None:
        self._handlers: list[tuple[str, SignalHandler]] = []
        self._queue: asyncio.Queue[Signal] = asyncio.Queue()
        self._dispatcher_task: asyncio.Task | None = None
        self._shutdown = asyncio.Event()

    async def start(self) -> None:
        self._dispatcher_task = asyncio.create_task(self._run_dispatcher())

    async def publish(self, signal: Signal) -> None:
        await self._queue.put(signal)

    def subscribe(self, topic_pattern: str, handler: SignalHandler) -> None:
        self._handlers.append((topic_pattern, handler))

    async def _run_dispatcher(self) -> None:
        while not self._shutdown.is_set():
            try:
                signal = await asyncio.wait_for(self._queue.get(), timeout=0.5)
            except asyncio.TimeoutError:
                continue
            for pattern, handler in self._handlers:
                if self._matches(pattern, signal.topic):
                    asyncio.create_task(self._safe_invoke(handler, signal))

    async def _safe_invoke(self, handler: SignalHandler, signal: Signal) -> None:
        try:
            await handler(signal)
        except Exception:  # noqa: BLE001
            from tsukuyomi.observability.logging import get_logger
            get_logger(__name__).exception("nervecore handler failed", topic=signal.topic)

    @staticmethod
    def _matches(pattern: str, topic: str) -> bool:
        if pattern == topic or pattern == "*":
            return True
        if pattern.endswith(".*"):
            return topic.startswith(pattern[:-1])
        return False

    async def shutdown(self) -> None:
        self._shutdown.set()
        if self._dispatcher_task:
            await self._dispatcher_task
