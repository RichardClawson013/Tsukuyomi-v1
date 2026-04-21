# Implementation How-To (Technical)

This file tells you exactly what to build in code and where.

## A) Gary: replace stub executor

### Code areas
- `src/tsukuyomi/protocols/gary.py`
- `src/tsukuyomi/core/config.py` (provider/audit config)
- `src/tsukuyomi/interceptor/*` (shared HTTP client patterns)

### Implementation notes
1. Add `AuditExecutor` protocol with method:
   - `ask(questions, action_summary, feedback, context) -> answers, cost`
2. Implement at least one real backend adapter.
3. Keep strict deterministic validator as gatekeeper (already present).
4. Add cost guard:
   - abort audit if cumulative cost exceeds `max_cost_per_audit_usd`.
5. Persist structured failure reasons as already done.

### Tests required
- backend success -> PASS
- backend evasive answers -> ESCALATED
- backend timeout/error -> deterministic safe behavior

## B) Shoulders: real blast radius

### Code areas
- `src/tsukuyomi/organs/shoulders.py`

### Implementation notes
1. Replace regex target extraction with parser over tool-call args + user intent.
2. Implement actual MCP call path:
   - process startup lifecycle
   - capability check
   - timeout handling
3. Risk mapping rules should be explicit and unit-tested.

### Tests required
- no target found -> UNKNOWN fallback
- MCP unavailable -> configured conservative risk
- MCP success -> expected risk bucket

## C) Mouth: webhook mode

### Code areas
- `src/tsukuyomi/organs/mouth.py`
- add `src/tsukuyomi/organs/mouth_webhook.py`

### Implementation notes
1. Signed payload (HMAC) both directions.
2. Correlation IDs for each approval request.
3. Explicit timeout and default behavior (`deny`) preserved.

### Tests required
- valid signed approval
- invalid signature rejected
- timeout -> default applied

## D) Toe + interceptor usage accounting

### Code areas
- `src/tsukuyomi/interceptor/server.py`
- `src/tsukuyomi/organs/toe.py`

### Implementation notes
1. Parse usage tokens from upstream responses where available.
2. Call `toe.record_actual(...)` post-response.
3. Include accounting in logs/metrics.

### Tests required
- usage present -> budget updates
- usage absent -> safe fallback without crash
- crossing thresholds changes zone behavior

## E) Eyes + Nose wiring

### Code areas
- `src/tsukuyomi/core/arbiter.py`
- `src/tsukuyomi/interceptor/server.py`

### Implementation notes
1. Feed tool call / command streams into Nose observers.
2. Wire Eyes verification when file-writing actions complete.
3. Escalate repeated mismatches according to config.

## F) NightShift heuristics

### Code areas
- `src/tsukuyomi/protocols/nightshift.py`

### Implementation notes
Implement at least these stubs:
- `audit_evasion_patterns`
- `skin_classification_drift`
- `budget_calibration`

Output should remain recommendation-only, never auto-apply.

## G) Observability endpoint

### Code areas
- `src/tsukuyomi/observability/metrics.py`
- `src/tsukuyomi/interceptor/server.py`

### Implementation notes
- expose `/metrics` when enabled
- publish decision counters and latencies
- ensure no sensitive payload leakage
