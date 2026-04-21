# 06 — Observability

**Document type:** Component specification
**Audience:** Engineers operating Tsukuyomi or building dashboards
**Prerequisites:** `01_overview.md`, `05_memory.md`
**Reading time:** 15 minutes

---

## 1. Three observability surfaces

Tsukuyomi exposes operational state through three surfaces, each with a different purpose, audience, and retention:

| Surface | Purpose | Audience | Retention |
| --- | --- | --- | --- |
| **Structured logs** | Per-event narrative; debugging | Operator, NightShift | 365 days (in `data/logs/`) and indexed in anatomic memory |
| **Metrics** | Time-series aggregates; dashboards | Operator | Exporter-defined (Prometheus default 15 days) |
| **Traces** | Per-request end-to-end timing | Operator (debugging hot paths) | Opt-in; sampled |

This document specifies each, the schema/format, and the operational expectations.

## 2. Structured logs

### 2.1 Format

Logs are line-delimited JSON (`.jsonl`), one event per line. The base record has mandatory fields:

```json
{
  "ts_utc": "2026-04-19T14:30:22.187Z",
  "level": "info",
  "request_id": "req_aB3xQ9",
  "organ": "shoulders",
  "decision": "high_risk",
  "reason": "blast_radius=14_callers",
  "latency_ms": 247,
  "version": "1.0.0",
  "schema_version": 1
}
```

Organ-specific fields go in a free `metadata` object:

```json
{
  ...,
  "organ": "shoulders",
  "metadata": {
    "target_symbol": "process_order",
    "direct_callers": 14,
    "affected_files": ["a.py", "b.py", "..."],
    "risk_rating": "HIGH"
  }
}
```

### 2.2 Logger configuration

Implementation uses `structlog` with these processors (in order):

1. `add_log_level` — derive `level` from the call site.
2. `TimeStamper(fmt='iso', utc=True)` — set `ts_utc`.
3. `KeyScrubFilter` — redact API key patterns from any string field. **This processor is mandatory; it must run before serialization. See §6.**
4. `EventVersionTagger` — set `schema_version`.
5. `JSONRenderer` — serialize.

The logger is configured at module import and used everywhere via `logger = structlog.get_logger(__name__)`.

### 2.3 Mandatory fields per organ

Each organ must include specific metadata fields in its log records, so that NightShift's pattern-mining can rely on schema-stable inputs. The contracts:

**Skin**: `tier`, `matched_rule_id` (or `null`), `classifier_confidence`, `classifier_top_class`.

**Ears**: `verdict`, `triggered_checks` (list).

**Shoulders**: `target_symbol`, `direct_callers`, `affected_files_count`, `risk_rating`, `gitnexus_latency_ms`.

**Knee**: `matched_pattern_id` (or `null`), `command_hash` (sha256, never the raw command at info-level — raw command is debug-level only and subject to redaction).

**Toe**: `zone`, `total_usd_today`, `model_requested`, `model_used`, `downgraded` (bool).

**Eyes**: `match_or_mismatch`, `expected_count`, `actual_count`, `surprise_files_count`.

**Nose**: `metric`, `value`, `threshold`, `severity`, `triggered_action`.

**Mouth**: `interface`, `triggering_organ`, `wait_seconds`, `decision`, `default_taken` (bool).

**Gary**: `audit_id`, `round`, `passed`, `failure_reasons` (list).

**Sandbox**: `sandbox_id`, `match_score`, `passed`, `cleanup_status`.

**Interceptor**: `inbound_format`, `upstream`, `tokens_in`, `tokens_out`, `cost_usd`, `latency_ms`, `final_decision`.

This contract is tested in `tests/integration/test_log_schema.py`.

### 2.4 File layout and rotation

```
data/logs/
  anatomy.jsonl                 (current day, append)
  anatomy-2026-04-18.jsonl.gz   (rotated, gzipped)
  anatomy-2026-04-17.jsonl.gz
  ...
```

Rotation: at 00:00 UTC, the current file is gzipped and date-stamped. Files older than `log_retention_days` (default 365) are deleted.

In parallel to file logging, every record is upserted into the `events` table of the anatomic memory, so that NightShift's queries see the same data through SQL.

## 3. Metrics

### 3.1 Format

OpenMetrics / Prometheus-compatible text format, exposed by the interceptor
when `observability.metrics_enabled=true`. The route path is
`observability.metrics_path` (default `/metrics`) on the same host/port as
the interceptor.

### 3.2 The metric set (v1.0)

```
# Counters
tsukuyomi_requests_total{tier,upstream,decision}
tsukuyomi_organ_decisions_total{organ,decision}
tsukuyomi_knee_blocks_total{pattern_id}
tsukuyomi_gary_audits_total{result}
tsukuyomi_sandbox_runs_total{passed}
tsukuyomi_mouth_prompts_total{interface,decision}
tsukuyomi_eyes_mismatches_total
tsukuyomi_nose_anomalies_total{metric,severity}

# Gauges
tsukuyomi_budget_usd_today{date}
tsukuyomi_budget_zone{zone}
tsukuyomi_pipeline_active_requests
tsukuyomi_memory_db_size_bytes
tsukuyomi_memory_wal_size_bytes

# Histograms
tsukuyomi_organ_latency_ms_bucket{organ}
tsukuyomi_upstream_latency_ms_bucket{upstream,model}
tsukuyomi_pipeline_total_latency_ms_bucket{tier}
tsukuyomi_audit_cost_usd_bucket
tsukuyomi_sandbox_duration_seconds_bucket
```

### 3.3 Recommended dashboards

`docs/dashboards/grafana/` contains importable JSON for:

- **Operations** — request rate, error rate, p50/p95/p99 latency by organ, budget burn rate, current zone.
- **Safety posture** — Knee blocks/day, Gary audit pass rate, sandbox match-score distribution, Eyes mismatch rate.
- **NightShift** — proposals generated/day, applied/rejected ratio, heuristic firing distribution.

These are reference dashboards; operators are expected to adapt them.

## 4. Distributed traces

### 4.1 Why it is opt-in

End-to-end tracing imposes ~5–15% latency overhead and produces high-volume data that most local deployments do not need. It is invaluable when investigating a specific slow path or organ-interaction bug, and pointless otherwise.

### 4.2 OpenTelemetry integration

Tsukuyomi is instrumented with `opentelemetry-sdk`. With OTEL exporters configured, every HTTP request becomes a trace with a span per organ:

```
pipeline_request                          487ms total
├── interceptor.parse_inbound              2ms
├── organ.skin                             1ms
├── organ.ears                             3ms
├── organ.shoulders                       249ms  (gitnexus_mcp_call)
├── protocol.gary                         186ms  (audit_llm_call)
│   ├── round_1                            89ms
│   └── round_2                            97ms
├── organ.sandbox                         (skipped — no file_writes)
├── organ.knee                              0ms
├── organ.toe                               1ms
├── interceptor.forward                    35ms
└── memory.write                           10ms
```

Configure via standard OTEL env vars (`OTEL_EXPORTER_OTLP_ENDPOINT` etc.). See `docs/guides/operations.md` §Tracing for setup.

### 4.3 Sampling

Default sampling: trace every Tier-3 request, 1% of Tier-1, 10% of Tier-2. Rationale: Tier-3 is rare and high-value to investigate; Tier-1 is high-volume and uniform.

## 5. The TUI dashboard

For interactive use Tsukuyomi ships a terminal UI based on Rich/Textual:

```bash
tsukuyomi dashboard
```

Panes:
- **Live request feed** (filterable by tier, organ, decision)
- **Current budget** (zone, today's spend, projected end-of-day)
- **Recent Gary audits** (pass/fail with click-through to transcripts)
- **Recent sandbox runs** (match-score histogram, last failures)
- **Mouth queue** (pending approval requests; respond directly)
- **NightShift proposals** (pending review)

The dashboard reads from the same anatomic memory and live event stream. It is read/respond-only — no destructive operations from the TUI.

## 6. Security: log scrubbing and PII

### 6.1 Mandatory scrubbing

Before any record is written (file, memory, metric label), `KeyScrubFilter` is applied:

- Strings matching common API key patterns (`sk-`, `sk-ant-`, JWTs) are replaced with `[REDACTED:KEY]`.
- Bearer tokens in `Authorization` headers are replaced with `[REDACTED:BEARER]`.
- Strings matching email patterns can optionally be replaced with `[REDACTED:EMAIL]` (disabled by default; enabled in compliance mode).

Scrubbing is unconditionally applied. Bypass requires a `--no-scrub` flag, which is gated behind an environment variable and only available in `local-dev` profile builds. **In any release build, `--no-scrub` is unavailable and ignored.**

### 6.2 What is and is not in logs

- **In logs**: organ decisions, model names, cost, latency, file *paths* (not content), command hashes (not raw commands at info level), error types and messages.
- **Not in logs by default**: full message bodies, full tool-call arguments, raw API keys, raw destructive commands above debug level, file content.
- **Configurable**: see `memory.retain_message_bodies` in `05_memory.md` §4 for the verbatim-retention opt-in.

## 7. Operational checklist

When something is wrong, the diagnostic path:

1. `tsukuyomi dashboard` — visual sanity check.
2. `tail -f data/logs/anatomy.jsonl | jq .` — last events.
3. `tsukuyomi memory inspect <request_id>` — full request record.
4. `tsukuyomi memory search --organ <organ> --since "1h"` — find related events.
5. Check Prometheus dashboards for systemic issues (latency spikes, error-rate jumps).
6. If tracing is enabled: pull the trace for the offending request from the OTEL backend.
7. If still unclear: turn on debug logging temporarily (`TSUKUYOMI_LOG_LEVEL=debug`) for the next session, then turn it off (debug logs are not redacted as aggressively and should not run continuously).

`docs/guides/troubleshooting.md` walks through specific symptoms and their probable causes.

---

*This concludes the architecture series. The remaining ADR documents in `../adr/` capture the specific decisions referenced throughout.*
