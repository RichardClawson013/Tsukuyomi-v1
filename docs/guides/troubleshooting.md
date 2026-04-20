# Troubleshooting

**Audience:** Anyone hitting a wall.
**Format:** Symptom → probable cause → fix.

---

## Symptom: Tsukuyomi will not start

**`address already in use`** — another process holds port 9999. Use `--port 9998` or stop the conflict (`lsof -i :9999`).

**`sqlite3.OperationalError`** — data directory not writable. Check perms.

**`pydantic.ValidationError` on startup** — `corelaw.json` invalid. Run `tsukuyomi config validate` to see the precise error.

**`ModuleNotFoundError: gitnexus`** — non-fatal. GitNexus not installed; Shoulders will return `UNKNOWN`. Install GitNexus or accept conservative fallback.

## Symptom: agent says "connection refused"

Tsukuyomi not running. Start it.

## Symptom: agent works but I see nothing in Tsukuyomi

Agent is not pointing at Tsukuyomi. Verify `echo $ANTHROPIC_BASE_URL` (or the equivalent for your agent). Re-export.

## Symptom: agent gets HTTP 401 from upstream

`ANTHROPIC_API_KEY` (or relevant) not set in Tsukuyomi's environment. Tsukuyomi-side, not agent-side.

## Symptom: every Tier-1 request is slow (> 100ms)

Memory writes are slow → check disk; SQLite WAL might need checkpointing (`tsukuyomi memory rotate`).

## Symptom: Protocol Gary fails on every Tier-3 request

Audit LLM endpoint unavailable or rejecting. Check `protocols.gary.fallback_audit_endpoint`.

## Symptom: Sandbox times out frequently

Repo too large; default time limit too tight. Increase `organs.sandbox.timeout_seconds` and/or set `sandbox.scope_to_modified_paths: true`.

## Symptom: NightShift produces no proposals

Insufficient data (< 24h of operation), or no patterns met thresholds. This is normal early on. Logs at `data/logs/nightshift.jsonl`.

## Symptom: budget RED zone reached very fast

`organs.toe.daily_budget_usd` too low for your usage, or runaway loop happened. Check `tsukuyomi memory search --organ toe --since "1d"` for the transition history.

## Symptom: Mouth never prompts me

`organs.mouth.interface` set to a webhook that's not reachable, or to `cli` but Tsukuyomi running headless. Switch interface or check the webhook.

## Symptom: agent's session dies mid-task with cryptic error

Tsukuyomi blocked something. Check `data/logs/anatomy.jsonl` for the latest `decision=block` event. The reason is logged.

## Symptom: I disagree with a Knee block

Either:
- Your operation is genuinely safe and the rule is too broad → file a NightShift-style proposal: edit the relevant rule with a comment explaining the carve-out, commit with a reasoned message.
- The rule is correct and your operation is not as safe as you think → reconsider, or use Mouth approval to override after explicit consideration.

Never silently widen rules without an ADR amendment. Tsukuyomi's safety property depends on the audit trail of rule changes.

## Symptom: I want to disable Tsukuyomi temporarily

`unset ANTHROPIC_BASE_URL` (or your equivalent). Re-export to re-engage. **No silent bypass mechanism exists by design.**

## Symptom: Tsukuyomi crashes

Reproduce with `--log-level=debug`, capture the traceback, file an issue at github.com/robdevet/tsukuyomi with: Tsukuyomi version, Python version, OS, redacted log excerpt.

## Symptom: my question is not here

Open an issue or discussion on the repo.
