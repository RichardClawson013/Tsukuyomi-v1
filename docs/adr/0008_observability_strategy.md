# ADR 0008: Three-Surface Observability — Structured Logs, Metrics, Optional Traces

| Field | Value |
| --- | --- |
| **Status** | Accepted |
| **Date** | 2026-04-19 |

## Context

Tsukuyomi must be observable to be operable, debuggable, and scientifically studyable. Observability also has costs: latency, storage, complexity, and the risk of leaking sensitive data into logs.

## Decision

Three observability surfaces with distinct purposes:

1. **Structured JSON logs** (always-on, mandatory). Every organ decision and every protocol step is logged. Format: line-delimited JSON with mandatory fields. Stored in `data/logs/` (rotated daily, retained 365 days) and indexed in anatomic memory.
2. **Prometheus-format metrics** (opt-in, exposed at `/metrics` if enabled). Counters, gauges, histograms per the metric set in `docs/architecture/06_observability.md` §3.2.
3. **OpenTelemetry traces** (opt-in, off by default, sampled when on). End-to-end timing for debugging hot paths.

All three apply mandatory key-scrubbing before write (KeyScrubFilter, ADR 0008-A).

## Rationale

Different observability needs warrant different surfaces:

- **Logs answer "what happened in this specific case."** Always needed; cheap to write; expensive (in storage) over time, addressed by retention.
- **Metrics answer "what's the rate / aggregate over time."** Cheap to compute; cheap to store; not always needed (developer workstation often has no Prometheus).
- **Traces answer "where did the time go in this specific request."** Expensive (per-span overhead); only needed sometimes; sampling makes it tractable.

Forcing all users to run all three is wasteful. Making logs mandatory and the others opt-in matches the cost model.

## Consequences

**Positive**: each user pays only for the observability they use; logs always available for incident investigation.

**Negative**: trace data is not retroactive — if an incident happens with tracing off, the trace is gone.

## Compliance

Every organ MUST emit a structured log on its decision (info-level) and on its errors (error-level) with the mandatory fields per `06_observability.md` §2.3. PRs missing these are rejected by the schema test in `tests/integration/test_log_schema.py`.
