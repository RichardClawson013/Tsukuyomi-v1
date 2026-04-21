"""SQLite + FTS5 implementation of MemoryBackend.

ADR 0002. WAL mode for concurrent reader (NightShift) + writer (Tsukuyomi).
"""
from __future__ import annotations
import json
import sqlite3
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import aiosqlite

from tsukuyomi.core.types import CanonicalRequest

SCHEMA_FILE = Path(__file__).parent / "schema.sql"


class SQLiteMemoryBackend:
    def __init__(self, mem_config: Any) -> None:
        self.path = Path(mem_config.sqlite_path).expanduser()
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.wal = bool(mem_config.wal_mode)
        self._db: aiosqlite.Connection | None = None

    async def initialize(self) -> None:
        self._db = await aiosqlite.connect(str(self.path))
        if self.wal:
            await self._db.execute("PRAGMA journal_mode=WAL")
        schema = SCHEMA_FILE.read_text() if SCHEMA_FILE.exists() else _SCHEMA_FALLBACK
        await self._db.executescript(schema)
        await self._db.commit()

    async def shutdown(self) -> None:
        if self._db:
            await self._db.close()

    async def write_request(self, req: CanonicalRequest) -> None:
        assert self._db
        await self._db.execute(
            """INSERT OR REPLACE INTO requests
               (request_id, ts_start_utc, ts_end_utc, inbound_format, agent_hint,
                model_requested, model_used, upstream, tier, tokens_in, tokens_out,
                cost_usd, latency_ms, final_decision, block_reason)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (
                req.request_id,
                req.received_at.isoformat(),
                CanonicalRequest.now().isoformat(),
                req.inbound_format,
                req.agent_hint,
                req.model_requested,
                req.model_used,
                None,                              # upstream filled in by interceptor.forward
                req.tier.value if req.tier else None,
                req.tokens_in,
                req.tokens_out,
                req.cost_usd,
                None,                              # latency
                req.final_decision.value if req.final_decision else None,
                req.block_reason,
            ),
        )
        await self._db.commit()

    async def write_event(self, *, organ: str, severity: str, decision: str | None,
                          reason: str | None, request_id: str | None,
                          metadata: dict[str, Any]) -> None:
        assert self._db
        await self._db.execute(
            """INSERT INTO events (event_id, ts_utc, request_id, organ, severity, decision, reason, metadata_json)
               VALUES (?,?,?,?,?,?,?,?)""",
            (
                str(uuid.uuid4()),
                datetime.now(timezone.utc).isoformat(),
                request_id, organ, severity, decision, reason,
                json.dumps(metadata, default=str),
            ),
        )
        await self._db.commit()

    async def write_audit(self, audit: dict[str, Any]) -> None:
        assert self._db
        await self._db.execute(
            """INSERT INTO audits
               (audit_id, request_id, ts_utc, action_summary, triggering_organ,
                rounds_json, final_decision, mouth_escalation, human_override,
                audit_cost_usd, audit_latency_seconds)
               VALUES (?,?,?,?,?,?,?,?,?,?,?)""",
            (
                audit["audit_id"], audit["request_id"], audit["ts_utc"],
                audit.get("action_summary"), audit.get("triggering_organ"),
                json.dumps(audit.get("rounds", []), default=str),
                audit.get("final_decision"),
                audit.get("mouth_escalation"),
                int(bool(audit.get("human_override", 0))),
                audit.get("audit_cost_usd", 0.0),
                audit.get("audit_latency_seconds", 0.0),
            ),
        )
        await self._db.commit()

    async def write_sandbox_run(self, run: dict[str, Any]) -> None:
        assert self._db
        await self._db.execute(
            """INSERT INTO sandbox_runs
               (sandbox_id, request_id, ts_start_utc, ts_end_utc,
                plan_json, expected_files_json, actual_files_json,
                match_score, passed, cleanup_status)
               VALUES (?,?,?,?,?,?,?,?,?,?)""",
            (
                run["sandbox_id"], run["request_id"], run["ts_start_utc"],
                run.get("ts_end_utc"),
                json.dumps(run.get("plan", {}), default=str),
                json.dumps(run.get("expected_files", []), default=str),
                json.dumps(run.get("actual_files", []), default=str),
                run.get("match_score", 0.0),
                int(bool(run.get("passed", False))),
                run.get("cleanup_status", "unknown"),
            ),
        )
        await self._db.commit()

    async def query_events(self, *, since_iso: str, organ: str | None = None,
                           decision: str | None = None) -> list[dict[str, Any]]:
        assert self._db
        sql = "SELECT * FROM events WHERE ts_utc >= ?"
        params: list[Any] = [since_iso]
        if organ:
            sql += " AND organ = ?"; params.append(organ)
        if decision:
            sql += " AND decision = ?"; params.append(decision)
        sql += " ORDER BY ts_utc DESC LIMIT 1000"
        async with self._db.execute(sql, params) as cur:
            cols = [d[0] for d in cur.description]
            return [dict(zip(cols, row)) async for row in cur]

    async def search_full_text(self, query: str, *, table: str = "events_fts") -> list[dict[str, Any]]:
        assert self._db
        sql = f"SELECT * FROM {table} WHERE {table} MATCH ? LIMIT 200"
        async with self._db.execute(sql, (query,)) as cur:
            cols = [d[0] for d in cur.description]
            return [dict(zip(cols, row)) async for row in cur]


_SCHEMA_FALLBACK = """-- minimal fallback if schema.sql is missing in deployment
CREATE TABLE IF NOT EXISTS events (event_id TEXT PRIMARY KEY, ts_utc TEXT, request_id TEXT, organ TEXT, severity TEXT, decision TEXT, reason TEXT, metadata_json TEXT);
CREATE TABLE IF NOT EXISTS requests (request_id TEXT PRIMARY KEY, ts_start_utc TEXT, ts_end_utc TEXT, inbound_format TEXT, agent_hint TEXT, model_requested TEXT, model_used TEXT, upstream TEXT, tier INTEGER, tokens_in INTEGER, tokens_out INTEGER, cost_usd REAL, latency_ms INTEGER, final_decision TEXT, block_reason TEXT);
CREATE TABLE IF NOT EXISTS audits (audit_id TEXT PRIMARY KEY, request_id TEXT, ts_utc TEXT, action_summary TEXT, triggering_organ TEXT, rounds_json TEXT, final_decision TEXT, mouth_escalation TEXT, human_override INTEGER, audit_cost_usd REAL, audit_latency_seconds REAL);
CREATE TABLE IF NOT EXISTS sandbox_runs (sandbox_id TEXT PRIMARY KEY, request_id TEXT, ts_start_utc TEXT, ts_end_utc TEXT, plan_json TEXT, expected_files_json TEXT, actual_files_json TEXT, match_score REAL, passed INTEGER, cleanup_status TEXT);
"""
