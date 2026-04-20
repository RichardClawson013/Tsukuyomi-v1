"""Shoulders — blast-radius analysis.

Uses GitNexus MCP for code-intelligence. Conservative on unavailability.
Spec: docs/architecture/03_organs.md §4.3.
"""
from __future__ import annotations
import asyncio
import json
import os
import re
from typing import Any

from tsukuyomi.core.types import BlastRadius, BlastRisk, CanonicalRequest
from tsukuyomi.observability.logging import get_logger

log = get_logger(__name__)


_SYMBOL_MENTION = re.compile(r"\b([A-Za-z_][A-Za-z_0-9]*)\b")


class Shoulders:
    def __init__(self, config: Any) -> None:
        self.config = config
        self._mcp_proc: asyncio.subprocess.Process | None = None
        self._mcp_ready = False

    async def analyze(self, req: CanonicalRequest) -> None:
        target = self._extract_target_symbol(req)
        if not target:
            req.blast_radius = BlastRadius.unknown("unknown_target")
            log.info("shoulders.analyze", request_id=req.request_id, target_symbol=None,
                     direct_callers=0, risk_rating="UNKNOWN", reason="no_target_extracted")
            return

        radius = await self._query_gitnexus(target)
        if radius is None:
            unknown_as = getattr(self.config, "unknown_treated_as", "HIGH")
            radius = BlastRadius(target_symbol=target, direct_callers=0,
                                 affected_files=[], risk=BlastRisk(unknown_as))
            log.warning("shoulders.gitnexus_unavailable",
                        request_id=req.request_id, target_symbol=target,
                        fallback_risk=unknown_as)
        req.blast_radius = radius
        log.info("shoulders.analyze", request_id=req.request_id,
                 target_symbol=radius.target_symbol, direct_callers=radius.direct_callers,
                 affected_files_count=len(radius.affected_files),
                 risk_rating=radius.risk.value)

    def _extract_target_symbol(self, req: CanonicalRequest) -> str | None:
        # Placeholder heuristic — real extraction should look at explicit tool args.
        text = ""
        for m in reversed(req.messages):
            if m.role == "user":
                text = m.content or ""; break
        m = re.search(r"\brename\s+([A-Za-z_][A-Za-z_0-9]*)\b", text, re.IGNORECASE)
        if m:
            return m.group(1)
        m = re.search(r"\bfunction\s+([A-Za-z_][A-Za-z_0-9]*)\b", text, re.IGNORECASE)
        if m:
            return m.group(1)
        return None

    async def _query_gitnexus(self, target: str) -> BlastRadius | None:
        # Minimal MCP stdio handshake — stub; real impl uses mcp sdk.
        # On any error, return None so caller applies conservative fallback.
        try:
            if not self._mcp_ready:
                await self._start_mcp()
            if not self._mcp_ready:
                return None
            # For v1.0 we return a pessimistic radius without actual MCP call.
            # A full MCP client lives in mcp_client.py (out of scope for this file).
            return BlastRadius(target_symbol=target, direct_callers=0,
                               affected_files=[], risk=BlastRisk.UNKNOWN)
        except Exception as exc:
            log.warning("shoulders.gitnexus_error", error=str(exc))
            return None

    async def _start_mcp(self) -> None:
        cmd = getattr(self.config, "mcp_command", None)
        if not cmd:
            return
        try:
            self._mcp_proc = await asyncio.create_subprocess_exec(
                *cmd, stdin=asyncio.subprocess.PIPE, stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            self._mcp_ready = True
        except FileNotFoundError:
            log.info("shoulders.mcp_not_installed", cmd=cmd)
            self._mcp_ready = False
