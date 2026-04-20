-- Tsukuyomi anatomic-memory schema (v1.0)
-- ADR 0002. SQLite + FTS5.

CREATE TABLE IF NOT EXISTS events (
  event_id        TEXT PRIMARY KEY,
  ts_utc          TEXT NOT NULL,
  request_id      TEXT,
  organ           TEXT NOT NULL,
  severity        TEXT NOT NULL,
  decision        TEXT,
  reason          TEXT,
  metadata_json   TEXT
);
CREATE INDEX IF NOT EXISTS idx_events_ts ON events(ts_utc);
CREATE INDEX IF NOT EXISTS idx_events_organ ON events(organ);
CREATE INDEX IF NOT EXISTS idx_events_request ON events(request_id);

CREATE VIRTUAL TABLE IF NOT EXISTS events_fts USING fts5(
  reason, metadata_json,
  content='events', content_rowid='rowid'
);

CREATE TRIGGER IF NOT EXISTS events_ai AFTER INSERT ON events BEGIN
  INSERT INTO events_fts(rowid, reason, metadata_json) VALUES (new.rowid, new.reason, new.metadata_json);
END;

CREATE TABLE IF NOT EXISTS requests (
  request_id      TEXT PRIMARY KEY,
  ts_start_utc    TEXT NOT NULL,
  ts_end_utc      TEXT,
  inbound_format  TEXT,
  agent_hint      TEXT,
  model_requested TEXT,
  model_used      TEXT,
  upstream        TEXT,
  tier            INTEGER,
  tokens_in       INTEGER,
  tokens_out      INTEGER,
  cost_usd        REAL,
  latency_ms      INTEGER,
  final_decision  TEXT,
  block_reason    TEXT
);
CREATE INDEX IF NOT EXISTS idx_requests_ts ON requests(ts_start_utc);
CREATE INDEX IF NOT EXISTS idx_requests_tier ON requests(tier);

CREATE TABLE IF NOT EXISTS audits (
  audit_id        TEXT PRIMARY KEY,
  request_id      TEXT NOT NULL,
  ts_utc          TEXT NOT NULL,
  action_summary  TEXT,
  triggering_organ TEXT,
  rounds_json     TEXT,
  final_decision  TEXT,
  mouth_escalation TEXT,
  human_override  INTEGER,
  audit_cost_usd  REAL,
  audit_latency_seconds REAL
);

CREATE VIRTUAL TABLE IF NOT EXISTS audits_fts USING fts5(
  action_summary, rounds_json,
  content='audits', content_rowid='rowid'
);

CREATE TRIGGER IF NOT EXISTS audits_ai AFTER INSERT ON audits BEGIN
  INSERT INTO audits_fts(rowid, action_summary, rounds_json)
    VALUES (new.rowid, new.action_summary, new.rounds_json);
END;

CREATE TABLE IF NOT EXISTS sandbox_runs (
  sandbox_id      TEXT PRIMARY KEY,
  request_id      TEXT NOT NULL,
  ts_start_utc    TEXT NOT NULL,
  ts_end_utc      TEXT,
  plan_json       TEXT,
  expected_files_json TEXT,
  actual_files_json   TEXT,
  match_score     REAL,
  passed          INTEGER,
  cleanup_status  TEXT
);

CREATE TABLE IF NOT EXISTS budget_state_history (
  transition_id   TEXT PRIMARY KEY,
  ts_utc          TEXT NOT NULL,
  date            TEXT NOT NULL,
  from_zone       TEXT,
  to_zone         TEXT NOT NULL,
  total_usd_at_transition REAL,
  request_id      TEXT
);

CREATE TABLE IF NOT EXISTS proposals (
  proposal_id     TEXT PRIMARY KEY,
  ts_generated_utc TEXT NOT NULL,
  heuristic       TEXT NOT NULL,
  status          TEXT NOT NULL,
  path            TEXT NOT NULL,
  supporting_event_ids_json TEXT,
  reviewed_by     TEXT,
  reviewed_ts_utc TEXT
);
