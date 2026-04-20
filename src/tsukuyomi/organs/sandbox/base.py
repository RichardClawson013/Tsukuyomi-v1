"""SandboxBackend protocol — swappable backends per ADR 0003."""
from __future__ import annotations
from typing import Protocol

from tsukuyomi.core.types import CanonicalRequest, SandboxResult


class SandboxBackend(Protocol):
    async def simulate(self, req: CanonicalRequest) -> SandboxResult: ...
