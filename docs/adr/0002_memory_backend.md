# ADR 0002: SQLite + FTS5 as the Anatomic-Memory Backend (v1.0)

| Field | Value |
| --- | --- |
| **Status** | Accepted (v1.0); revisit for v2.0 |
| **Date** | 2026-04-19 |
| **Decision-makers** | Rob de Vet |
| **Consulted** | Claude (Anthropic), GBrain (Garry Tan), Graphiti documentation |
| **Informed** | NightShift contributors, v2.0 enterprise track |

## Context

Tsukuyomi requires persistent storage for its anatomic memory: organ decisions, audit transcripts, sandbox results, budget state, NightShift proposals. Volume estimate: ~10–100K events/day for a single-developer workstation, ~1–10M/day for a team-scale deployment. Access pattern: append-mostly, read-many (NightShift, dashboard, debugging).

Relevant requirements:
- Zero operational overhead for the developer-workstation case.
- Full-text search over reason fields and audit transcripts (NightShift).
- Deterministic, ACID, single-machine.
- Replaceable for v2.0 multi-tenant scenarios without forcing a v1.0 redesign.

## Decision

**SQLite with FTS5** for v1.0. Schema in `src/tsukuyomi/memory/schema.sql`. WAL mode for concurrent reader (NightShift) + writer (Tsukuyomi).

The memory module exposes a small interface (`MemoryBackend` in `src/tsukuyomi/memory/base.py`) so v2.0 can swap to Postgres without touching organs or protocols.

## Rationale

1. **Zero-ops.** SQLite is single-file, no daemon. `python -m sqlite3` is in stdlib. New users get a functioning memory store with no external install.
2. **FTS5 is production-grade.** Full-text search ranks comparably to Elasticsearch for our access pattern (operational logs and audit text).
3. **ACID and predictable.** No concurrent-write conflicts to reason about (Tsukuyomi has one writer per instance).
4. **Continuity.** v0.0 used JSON files; SQLite is the natural progression, not a leap.
5. **Backup is `cp`.** Operationally trivial.

## Alternatives considered

### Graphiti (`getzep/graphiti`)

**Rejected.** Graphiti is a bi-temporal knowledge graph, designed for entity-relationship-rich agent memory (people, events, facts that evolve). Tsukuyomi's anatomic memory is structurally an audit log — flat, append-mostly, with no entity-graph semantics. The temporal-graph features would be unused; the operational overhead (graph DB dependency: FalkorDB, Neo4j, or Kuzu) would be paid in full.

### GBrain (`garrytan/gbrain`)

**Considered and rejected for this use case, but architecturally aligned.** GBrain solves *personal knowledge* with hybrid search (Postgres + pgvector + tsvector + RRF fusion). It is excellent for that purpose. For Tsukuyomi's anatomic memory specifically — operational telemetry, not curated knowledge — the Postgres dependency is operationally heavy for the developer-workstation scenario, and the vector-search component is unused (Tsukuyomi's queries are structured aggregations and FTS, not semantic similarity).

GBrain's design influenced our memory schema (the principle of clean separation between structured fields and full-text-searchable text). For users who *want* GBrain to be the anatomic-memory backend, the v1.1 pluggable backends will support a `gbrain://` URI.

### Postgres with pgvector

**Deferred to v2.0.** Appropriate for multi-tenant enterprise deployment. Operationally heavy for v1.0 single-developer scenario.

### JSONL files only (no DB)

**Rejected.** NightShift's pattern-mining requires queries beyond `grep` and `awk`. At operational scale (months of data) JSONL becomes unmanageable.

### DuckDB

**Considered.** Equivalent on most criteria. Chose SQLite because `sqlite3` is in the Python stdlib while DuckDB requires a separate install. A safety system should minimize dependencies.

## Consequences

### Positive

- Zero install friction.
- Backup, restore, and inspect are trivial (`cp`, `sqlite3` shell, `tsukuyomi memory inspect`).
- Full-text search via FTS5.
- Production-tested at gigabyte scale.

### Negative

- Single-writer constraint: not suitable for multi-tenant write traffic. Mitigated by the v2.0 path to Postgres.
- No native vector search. Our access pattern doesn't need it; if it does in future, FTS5 + a separate vector index file is feasible, or a backend swap.
- WAL file management on aggressive write loads requires checkpointing tuning (handled in `tsukuyomi memory rotate`).

## Migration path to v2.0

The `MemoryBackend` interface defines:

```python
class MemoryBackend(Protocol):
    async def write_event(self, event: Event) -> None: ...
    async def write_request(self, req: RequestRecord) -> None: ...
    async def write_audit(self, audit: AuditRecord) -> None: ...
    async def query_events(self, ...) -> list[Event]: ...
    async def search_full_text(self, query: str, ...) -> list[SearchHit]: ...
    async def aggregate(self, ...) -> ...: ...
```

A `PostgresBackend` implementing this interface is a v2.0 deliverable. NightShift heuristics that use raw SQL (a small subset) will need backend-specific dialect handling at that point.
