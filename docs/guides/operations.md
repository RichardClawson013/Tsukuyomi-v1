# Operations Guide

**Audience:** Anyone running Tsukuyomi past the first day.

---

## 1. Daily routine

### Morning
- `tsukuyomi dashboard` — quick visual sanity check.
- Review `data/proposals/$(date -d yesterday +%F)/` for NightShift proposals.
- Apply, reject, or defer each proposal (see `04_protocols.md` §5.2).

### During work
- Tsukuyomi runs in the background.
- Mouth approval prompts appear in your TUI dashboard or per your configured interface.

### Evening
- `tsukuyomi memory stats` to see the day's volume.
- NightShift will run automatically at 03:00 (or your configured time).

## 2. Monitoring

### Health endpoint
```bash
curl http://localhost:9999/health
# {"status":"ok","version":"1.0.0","uptime_seconds":86400,"organs":{...}}
```

### Metrics (if enabled)
```bash
curl http://localhost:9999/metrics | rg tsukuyomi_
```

If you changed `observability.metrics_path`, use that path instead.

### Live log
```bash
tail -f ~/.local/share/tsukuyomi/data/logs/anatomy.jsonl | jq .
```

### Recent blocks
```bash
tsukuyomi memory search --organ knee --decision block --since "1d"
```

## 3. Backup

The anatomic memory and config should be backed up. Daily snapshot:

```bash
tsukuyomi memory backup --output /backup/tsukuyomi/$(date +%F).db
cp -a ~/.local/share/tsukuyomi/config/ /backup/tsukuyomi/config-$(date +%F)/
```

Restore:

```bash
tsukuyomi stop
cp /backup/tsukuyomi/2026-04-19.db ~/.local/share/tsukuyomi/data/memory.db
tsukuyomi start
```

## 4. Upgrading

```bash
tsukuyomi stop
pip install -U tsukuyomi
tsukuyomi config migrate           # apply schema migrations
tsukuyomi memory migrate           # apply DB schema migrations
tsukuyomi start
```

## 5. Mouth — handling approval prompts

When Tsukuyomi escalates to the Mouth, the prompt appears in:
- The TUI dashboard's "Mouth queue" pane (interactive).
- The terminal where Tsukuyomi is running (CLI mode).
- A configured webhook (production mode).
- A watched file in `data/mouth/` (for headless deployments).

Decision options: `approve`, `deny`, `abort_all` (kills the requesting agent's session). Default on timeout: `deny`.

Recommended discipline: never approve without reading the full context (the audit transcript, the blast-radius report, the sandbox result). Tsukuyomi's job is to slow you down at exactly these moments.

## 6. Tracing

Enable for a debugging session:

```bash
export OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4318
tsukuyomi start --tracing-enabled
# ... reproduce the issue ...
# spans are at your OTLP backend (Jaeger, Tempo, etc.)
```

Turn off when not needed (overhead).

## 7. Performance tuning

If pipeline latency is too high:
1. Check `tsukuyomi memory stats` for organ latencies (p95).
2. The most common culprit is Shoulders (GitNexus); check that GitNexus index is fresh: `gitnexus analyze`.
3. Protocol Gary uses an LLM call; cost is intrinsic. Mitigate with cheaper audit endpoint.
4. Sandbox can be slow for large repos; configure `sandbox.scope_to_modified_paths: true`.

## 8. Multi-machine deployments

Not supported in v1.0. See `docs/architecture/01_overview.md` §5.3 and the v2.0 roadmap.

## 9. CI integration

Run Tsukuyomi as a sidecar in agent-running CI jobs:

```yaml
# example: GitHub Actions
services:
  tsukuyomi:
    image: tsukuyomi/tsukuyomi:1.0
    ports:
      - 9999:9999
    env:
      ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}

steps:
  - run: ANTHROPIC_BASE_URL=http://localhost:9999 your-agent ...
```

This catches agent-induced regressions in CI before they hit a developer's machine.

## 10. Acceptance gate (one command)

Use the acceptance gate script before public demos/releases:

```bash
scripts/acceptance_gate.sh
```

What it validates:
- unit-test suite passes
- smoke runtime checks pass (`scripts/smoke_test.sh`)
- core artifact paths are present (`data/audits`, `data/proposals`)

Common modes:

```bash
# Use existing running Tsukuyomi instance
scripts/acceptance_gate.sh

# Auto-start Tsukuyomi with explicit config
AUTO_START=1 \
SERVER_CMD='tsukuyomi start --config ~/.local/share/tsukuyomi/config/corelaw.json' \
scripts/acceptance_gate.sh
```
