"""Shoulders — blast-radius analysis via GitNexus MCP."""
from __future__ import annotations

import asyncio
import json
import re
from dataclasses import dataclass
from typing import Any, Protocol

from tsukuyomi.core.types import BlastRadius, BlastRisk, CanonicalRequest
from tsukuyomi.observability.logging import get_logger

log = get_logger(__name__)


class GitNexusClient(Protocol):
    async def get_impact(self, target: str) -> tuple[int, list[str]]:
        """Return (direct_callers, affected_files)."""

    async def close(self) -> None:
        """Shutdown/cleanup resources."""


@dataclass
class _McpJsonRpcState:
    request_counter: int = 0


class StdioGitNexusClient:
    def __init__(self, command: list[str], startup_timeout_seconds: int) -> None:
        self.command = command
        self.startup_timeout_seconds = startup_timeout_seconds
        self._proc: asyncio.subprocess.Process | None = None
        self._state = _McpJsonRpcState()
        self._lock = asyncio.Lock()

    async def get_impact(self, target: str) -> tuple[int, list[str]]:
        async with self._lock:
            await self._ensure_started()
            tools = await self._request("tools/list", {})
            tool_name = self._pick_tool_name(tools)
            args = {"target": target, "direction": "upstream"}
            result = await self._request("tools/call", {"name": tool_name, "arguments": args})
            return self._parse_impact(result)

    async def close(self) -> None:
        if self._proc is None:
            return
        proc = self._proc
        self._proc = None
        if proc.returncode is None:
            proc.terminate()
            try:
                await asyncio.wait_for(proc.wait(), timeout=2)
            except asyncio.TimeoutError:
                proc.kill()
                await proc.wait()

    async def _ensure_started(self) -> None:
        if self._proc and self._proc.returncode is None:
            return
        try:
            self._proc = await asyncio.wait_for(
                asyncio.create_subprocess_exec(
                    *self.command,
                    stdin=asyncio.subprocess.PIPE,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                ),
                timeout=self.startup_timeout_seconds,
            )
        except FileNotFoundError as exc:
            raise RuntimeError("GitNexus MCP command not found") from exc
        except asyncio.TimeoutError as exc:
            raise RuntimeError("GitNexus MCP startup timeout") from exc

        await self._request("initialize", {
            "protocolVersion": "2024-11-05",
            "clientInfo": {"name": "tsukuyomi", "version": "1.0.0"},
            "capabilities": {},
        })
        await self._notify("notifications/initialized", {})

    async def _notify(self, method: str, params: dict[str, Any]) -> None:
        if self._proc is None or self._proc.stdin is None:
            raise RuntimeError("GitNexus MCP process unavailable")
        payload = {"jsonrpc": "2.0", "method": method, "params": params}
        self._proc.stdin.write((json.dumps(payload) + "\n").encode())
        await self._proc.stdin.drain()

    async def _request(self, method: str, params: dict[str, Any]) -> dict[str, Any]:
        if self._proc is None or self._proc.stdin is None or self._proc.stdout is None:
            raise RuntimeError("GitNexus MCP process unavailable")
        self._state.request_counter += 1
        req_id = self._state.request_counter
        payload = {
            "jsonrpc": "2.0",
            "id": req_id,
            "method": method,
            "params": params,
        }
        self._proc.stdin.write((json.dumps(payload) + "\n").encode())
        await self._proc.stdin.drain()

        timeout = float(self.startup_timeout_seconds)
        while True:
            line = await asyncio.wait_for(self._proc.stdout.readline(), timeout=timeout)
            if not line:
                raise RuntimeError("GitNexus MCP closed stdout unexpectedly")
            msg = json.loads(line.decode())
            if msg.get("id") != req_id:
                # Ignore notifications/other async events.
                continue
            if "error" in msg:
                raise RuntimeError(f"GitNexus MCP error: {msg['error']}")
            result = msg.get("result")
            if not isinstance(result, dict):
                raise RuntimeError("GitNexus MCP malformed response")
            return result

    @staticmethod
    def _pick_tool_name(tools_payload: dict[str, Any]) -> str:
        tools = tools_payload.get("tools")
        if not isinstance(tools, list):
            raise RuntimeError("GitNexus MCP tools/list missing tools")
        names = [
            t.get("name")
            for t in tools
            if isinstance(t, dict) and isinstance(t.get("name"), str)
        ]
        for candidate in ("gitnexus_impact", "impact", "symbol_impact"):
            if candidate in names:
                return candidate
        raise RuntimeError(f"GitNexus impact tool not found in tools: {names}")

    @staticmethod
    def _parse_impact(result: dict[str, Any]) -> tuple[int, list[str]]:
        content = result.get("content")
        parsed: Any = None
        if isinstance(content, list):
            text_parts = [
                item.get("text", "")
                for item in content
                if isinstance(item, dict) and item.get("type") == "text"
            ]
            joined = "\n".join(text_parts).strip()
            if joined:
                try:
                    parsed = json.loads(joined)
                except json.JSONDecodeError:
                    parsed = None
        if parsed is None:
            parsed = result.get("structuredContent") or result
        if not isinstance(parsed, dict):
            raise RuntimeError("GitNexus impact response malformed")

        callers = (
            parsed.get("direct_callers")
            or parsed.get("caller_count")
            or parsed.get("impact_count")
            or 0
        )
        files = (
            parsed.get("affected_files")
            or parsed.get("files")
            or parsed.get("impacted_files")
            or []
        )
        if not isinstance(files, list):
            files = []
        out_files = [str(x) for x in files if isinstance(x, str)]
        return int(callers), out_files


class Shoulders:
    def __init__(self, config: Any, gitnexus_client: GitNexusClient | None = None) -> None:
        self.config = config
        self._client = gitnexus_client or StdioGitNexusClient(
            command=list(getattr(config, "mcp_command", [])),
            startup_timeout_seconds=int(getattr(config, "mcp_startup_timeout_seconds", 20)),
        )

    async def analyze(self, req: CanonicalRequest) -> None:
        target = self._extract_target_symbol(req)
        if not target:
            req.blast_radius = BlastRadius.unknown("unknown_target")
            log.info(
                "shoulders.analyze",
                request_id=req.request_id,
                target_symbol=None,
                direct_callers=0,
                risk_rating="UNKNOWN",
                reason="no_target_extracted",
            )
            return

        radius = await self._query_gitnexus(target)
        if radius is None:
            unknown_as = getattr(self.config, "unknown_treated_as", "HIGH")
            radius = BlastRadius(
                target_symbol=target,
                direct_callers=0,
                affected_files=[],
                risk=BlastRisk(unknown_as),
            )
            log.warning(
                "shoulders.gitnexus_unavailable",
                request_id=req.request_id,
                target_symbol=target,
                fallback_risk=unknown_as,
            )
        req.blast_radius = radius
        log.info(
            "shoulders.analyze",
            request_id=req.request_id,
            target_symbol=radius.target_symbol,
            direct_callers=radius.direct_callers,
            affected_files_count=len(radius.affected_files),
            risk_rating=radius.risk.value,
        )

    async def shutdown(self) -> None:
        await self._client.close()

    def _extract_target_symbol(self, req: CanonicalRequest) -> str | None:
        for m in reversed(req.messages):
            for tc in m.tool_calls:
                name = tc.get("name") if isinstance(tc, dict) else None
                args = tc.get("arguments") if isinstance(tc, dict) else None
                if isinstance(args, str):
                    try:
                        args = json.loads(args)
                    except json.JSONDecodeError:
                        args = {}
                if not isinstance(args, dict):
                    continue
                for key in ("target", "symbol", "function", "identifier", "name"):
                    val = args.get(key)
                    if isinstance(val, str) and val.strip() and self._looks_like_symbol(val):
                        return val.strip()
                if isinstance(name, str) and "rename" in name and isinstance(args.get("from"), str):
                    from_val = args.get("from")
                    if isinstance(from_val, str) and self._looks_like_symbol(from_val):
                        return from_val

        text = ""
        for m in reversed(req.messages):
            if m.role == "user":
                text = m.content or ""
                break
        patterns = [
            r"\brename\s+([A-Za-z_][A-Za-z_0-9]*)\b",
            r"\bfunction\s+([A-Za-z_][A-Za-z_0-9]*)\b",
            r"\b(?:refactor|modify|change|update)\s+([A-Za-z_][A-Za-z_0-9]*)\b",
        ]
        for pat in patterns:
            found = re.search(pat, text, re.IGNORECASE)
            if found:
                return found.group(1)
        return None

    async def _query_gitnexus(self, target: str) -> BlastRadius | None:
        try:
            direct_callers, files = await self._client.get_impact(target)
            return BlastRadius(
                target_symbol=target,
                direct_callers=int(direct_callers),
                affected_files=files,
                risk=self._risk_from_callers(int(direct_callers)),
            )
        except Exception as exc:  # noqa: BLE001
            log.warning("shoulders.gitnexus_error", error=str(exc))
            return None

    def _risk_from_callers(self, direct_callers: int) -> BlastRisk:
        thresholds = getattr(self.config, "thresholds", {}) or {}
        low_max = int(thresholds.get("low_max_callers", 0))
        med_max = int(thresholds.get("medium_max_callers", 5))
        high_max = int(thresholds.get("high_max_callers", 15))
        if direct_callers <= low_max:
            return BlastRisk.LOW
        if direct_callers <= med_max:
            return BlastRisk.MEDIUM
        if direct_callers <= high_max:
            return BlastRisk.HIGH
        return BlastRisk.CRITICAL

    @staticmethod
    def _looks_like_symbol(value: str) -> bool:
        return bool(re.fullmatch(r"[A-Za-z_][A-Za-z_0-9]*", value))
