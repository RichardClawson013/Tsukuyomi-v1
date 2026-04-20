# 05 — Anatomic Memory

**Document type:** Component specification
**Audience:** Engineers implementing memory backends or NightShift heuristics
**Prerequisites:** `01_overview.md`, `04_protocols.md`
**Reading time:** 20 minutes

---

## 1. The boundary between "Tsukuyomi's memory" and "the agent's memory"

This boundary is the most commonly misunderstood part of the architecture.

The **agent** (Claude Code, Hermes, etc.) typically has its own memory subsystem: Hermes has skills and episodic memory via its own backend; Claude Code has no persistent memory out of the box but can be augmented; Letta provides OS-inspired tiered memory.

**Tsukuyomi does not touch any of this.** Tsukuyomi has its own memory, called the **anatomic memory**, which stores data about *Tsukuyomi's own operation*:

- Every organ decision and the reasons for it.
- Every Protocol Gary audit transcript and validation outcome.
- Every sandbox simulation, its match-score, and its divergence from the declared plan.
- Every Knee block, with the matched pattern and the raw command.
- Every Toe zone transition, the cost state, and the model downgrade applied.
- Every Eyes verification result.
- Every Nose anomaly signal.
- Every Mouth approval request, the response, and the wait time.
- Every forward to upstream, the provider, the model, the latency, and the cost.

The agent knows none of this. The anatomic memory is Tsukuyomi looking at itself.

**Why this distinction matters:**

1. **Clean responsibilities.** The agent's job is to accomplish user tasks; its memory serves that. Tsukuyomi's job is to enforce safety; its memory serves NightShift's learning and audit/compliance use cases.
2. **Independent evolution.** The agent can be swapped out (Claude Code today, Hermes tomorrow) without affecting Tsukuyomi's historical record.
3. **Privacy posture.** Users may have legitimate reasons to redact memory from their agent (sensitive conversations). Tsukuyomi's anatomic memory contains *Tsukuyomi's* decisions, not the agent's conversational content — which has different handling (see Section 4, Redaction).

## 2. Backend choice: SQLite with FTS5

### Why SQLite

1. **Zero operational overhead.** No daemon to run, no connection pooling, no migration tooling beyond what ships with the `sqlite3` standard library module. A Tsukuyomi deployment on a developer workstation has no database dependency to install.
2. **Deterministic behavior.** SQLite is single-file, ACID, and predictable. No concurrent-access headaches for Tsukuyomi's access pattern (one writer per Tsukuyomi instance, NightShift reads separately). WAL mode handles the reader-writer case.
3. **Scale headroom.** Tsukuyomi's memory is operational metadata, not document storage. A year of busy operation produces tens of millions of rows at most; SQLite handles this comfortably.
4. **FTS5 full-text search.** For NightShift's pattern-mining heuristics, text search across audit transcripts and organ signal reasons is essential. FTS5 is the best open-source FTS engine, ships built-in with SQLite, and is free of the operational burden of Elasticsearch-class systems.
5. **Continuity with v0.0.** v0.0 already uses JSON state for budget and simple logging. SQLite is a natural progression, not a leap.

### What was considered and rejected

- **Graphiti** (`github.com/getzep/graphiti`) was considered. Rejected: Tsukuyomi's memory is audit log structure, not entity-relationship graph. The bi-temporal knowledge graph features are a mismatch for operational telemetry, and Graphiti requires a backing graph database (FalkorDB, Neo4j, or Kuzu). Full rationale: ADR `docs/adr/0002_memory_backend.md`.
- **Postgres with pgvector (à la GBrain)** was considered. Rejected: operational overhead too high for a per-developer local deployment. Postgres is appropriate for the v2.0 multi-tenant enterprise deployment scenario and will be added as a pluggable backend then.
- **JSONL files only, no database.** Considered; rejected because NightShift pattern-mining needs queries beyond what `grep` practically supports, and at operational scale the JSONL files would become unmanageable.
- **DuckDB.** Considered; equivalent on most criteria to SQLite. Chose SQLite because `sqlite3` is in the Python standard library while DuckDB requires a separate install — and a safety system should have minimal dependencies.

## 3. Schema

The schema is defined in `src/tsukuyomi/memory/schema.sql`. The essential tables:

### `events` — the core append-only event log

```sql
CREATE TABLE events (
  event_id        TEXT PRIMARY KEY,           -- uuid
  ts_utc          TEXT NOT NULL,              -- ISO-8601
  request_id      TEXT,                       -- links to upstream request
  organ           TEXT NOT NULL,              -- skin|ears|shoulders|knee|toe|eyes|nose|mouth|gary|sandbox|nightshift|interceptor
  severity        TEXT NOT NULL,              -- info|warn|error|critical
  decision        TEXT,                       -- permit|block|escalate|downgrade|...
  reason          TEXT,                       -- free text, searched by FTS
  metadata_json   TEXT                        -- JSON for organ-specific fields
);
CREATE INDEX idx_events_ts ON events(ts_utc);
CREATE INDEX idx_events_organ ON events(organ);
CREATE INDEX idx_events_request ON events(request_id);
```

### `events_fts` — FTS5 virtual table for full-text search

```sql
CREATE VIRTUAL TABLE events_fts USING fts5(
  reason, metadata_json,
  content='events', content_rowid='rowid'
);
-- triggers keep FTS in sync with the events table
```

### `requests` — one row per agent-originated HTTP request

```sql
CREATE TABLE requests (
  request_id      TEXT PRIMARY KEY,
  ts_start_utc    TEXT NOT NULL,
  ts_end_utc      TEXT,
  inbound_format  TEXT,                       -- anthropic|openai
  agent_hint      TEXT,
  model_requested TEXT,
  model_used      TEXT,                       -- after Toe possibly rewrote
  upstream        TEXT,                       -- anthropic|openai|openrouter|ollama|...
  tier            INTEGER,
  tokens_in       INTEGER,
  tokens_out      INTEGER,
  cost_usd        REAL,
  latency_ms      INTEGER,
  final_decision  TEXT,                       -- forwarded|blocked|escalated
  block_reason    TEXT
);
CREATE INDEX idx_requests_ts ON requests(ts_start_utc);
CREATE INDEX idx_requests_tier ON requests(tier);
```

### `audits` — one row per Protocol Gary audit

```sql
CREATE TABLE audits (
  audit_id        TEXT PRIMARY KEY,
  request_id      TEXT NOT NULL,
  ts_utc          TEXT NOT NULL,
  action_summary  TEXT,
  triggering_organ TEXT,
  rounds_json     TEXT,                       -- full round-by-round record
  final_decision  TEXT,                       -- PASS|BLOCK|ESCALATED
  mouth_escalation TEXT,                      -- approve|deny|timeout|null
  human_override  INTEGER,                    -- 0/1
  audit_cost_usd  REAL,
  audit_latency_seconds REAL,
  FOREIGN KEY (request_id) REFERENCES requests(request_id)
);
CREATE VIRTUAL TABLE audits_fts USING fts5(
  action_summary, rounds_json,
  content='audits', content_rowid='rowid'
);
```

### `sandbox_runs` — one row per Tsukuyomi sandbox simulation

```sql
CREATE TABLE sandbox_runs (
  sandbox_id      TEXT PRIMARY KEY,
  request_id      TEXT NOT NULL,
  ts_start_utc    TEXT NOT NULL,
  ts_end_utc      TEXT,
  plan_json       TEXT,
  expected_files_json TEXT,
  actual_files_json   TEXT,
  match_score     REAL,
  passed          INTEGER,                    -- 0/1
  cleanup_status  TEXT,                       -- clean|leaked|error
  FOREIGN KEY (request_id) REFERENCES requests(request_id)
);
```

### `budget_state_history` — Toe zone transitions

```sql
CREATE TABLE budget_state_history (
  transition_id   TEXT PRIMARY KEY,
  ts_utc          TEXT NOT NULL,
  date            TEXT NOT NULL,              -- YYYY-MM-DD
  from_zone       TEXT,
  to_zone         TEXT NOT NULL,
  total_usd_at_transition REAL,
  request_id      TEXT
);
```

### `proposals` — NightShift-produced proposals

```sql
CREATE TABLE proposals (
  proposal_id     TEXT PRIMARY KEY,
  ts_generated_utc TEXT NOT NULL,
  heuristic       TEXT NOT NULL,
  status          TEXT NOT NULL,              -- pending|applied|rejected|expired
  path            TEXT NOT NULL,              -- filesystem path to the .md
  supporting_event_ids_json TEXT,
  reviewed_by     TEXT,
  reviewed_ts_utc TEXT
);
```

## 4. Redaction and privacy

### What is stored in the clear

- Organ decisions and severity (no user content).
- Request metadata: model, timing, cost, upstream (no message bodies).
- Sandbox plans (hashes of paths, not content).
- NightShift proposals (derived patterns, not verbatim content).

### What is *not* stored by default

- **Message bodies.** The user's prompt and the agent's response are not persisted unless `memory.retain_message_bodies` is set (default: false). This is the conservative default for privacy: Tsukuyomi observes, it does not transcribe.
- **Tool-call arguments in full.** Only hashes and summaries, unless explicitly enabled for debugging.
- **API credentials.** Never logged. `KeyScrubFilter` in observability ensures key patterns are redacted before any write.

### When message bodies are retained

For `data_regulatory` deployments (audit requirements, compliance investigation) you can opt in to verbatim retention:

```json
"memory": {
  "retain_message_bodies": true,
  "retain_tool_call_args": true,
  "retention_days_bodies": 30,
  "encrypt_bodies_at_rest": true
}
```

In this mode, message bodies are stored in a separate table (`message_bodies`) with AES-GCM encryption using a key loaded from OS keyring; decryption requires explicit human-initiated access via `tsukuyomi memory inspect <request_id>`.

### Retention defaults

- `events`, `requests`, `audits`, `sandbox_runs`, `budget_state_history`: **365 days**.
- `proposals` (rejected): **180 days**; `proposals` (applied): **indefinite** (part of the change history).
- `message_bodies` (if enabled): **30 days** (shorter, given higher sensitivity).

Rotation is handled by `tsukuyomi memory rotate`, run nightly as part of the NightShift chain.

## 5. How NightShift queries this

NightShift uses two query styles:

**Aggregations for threshold heuristics:**

```sql
-- Heuristic: frequently_blocked_commands
SELECT
  json_extract(metadata_json, '$.blocked_pattern') AS pattern,
  json_extract(metadata_json, '$.command_hash') AS command_hash,
  COUNT(*) AS hits
FROM events
WHERE organ = 'knee'
  AND decision = 'block'
  AND ts_utc > datetime('now', '-24 hours')
GROUP BY pattern, command_hash
HAVING COUNT(*) >= :min_block_count;
```

**Full-text search for audit pattern analysis:**

```sql
-- Heuristic: audit_evasion_patterns
SELECT
  a.audit_id,
  json_extract(a.rounds_json, '$[0].answers') AS round1_answers
FROM audits a
JOIN audits_fts fts ON fts.rowid = a.rowid
WHERE audits_fts MATCH 'round1_failed'
  AND a.ts_utc > datetime('now', '-30 days');
```

The heuristic catalog — one per file, pluggable — lives in `src/tsukuyomi/protocols/nightshift/heuristics/`. Each heuristic declares its query, its threshold, and its proposal-template.

## 6. Operations

### Backup

SQLite databases are single files. Backup is a file copy of the database directory during a brief snapshot:

```bash
# tsukuyomi provides a safe snapshot command that uses SQLite's .backup
tsukuyomi memory backup --output /path/to/backup-$(date +%F).db
```

### Inspection

```bash
# Summary stats
tsukuyomi memory stats

# Inspect one request end-to-end
tsukuyomi memory inspect <request_id>

# Search events by reason
tsukuyomi memory search --organ knee --since "1 day ago"

# Explore via sqlite3 directly
sqlite3 data/memory.db
```

### Migration between versions

Each release ships a `migrations/` directory. `tsukuyomi memory migrate` applies pending migrations transactionally. Downgrades are not supported automatically; use a backup.

### WAL mode

SQLite is opened with `PRAGMA journal_mode=WAL` to enable concurrent readers (NightShift) while a writer (Tsukuyomi main process) is active. WAL checkpointing is triggered nightly or on 16MB WAL size, whichever first.

## 7. Observability of the memory itself

Memory is observed like any other component:

- Every write emits an `event` (meta-events about memory, tagged `organ='memory'`).
- Database size, write rate, and query latency are exported as metrics.
- A stuck writer (SQLite locked for > 30s) raises a Nose anomaly.

---

*Next: `06_observability.md` — structured logging, metrics, and tracing across the system.*
