# Known Limitations (Current State)

This file is intentionally explicit. Tsukuyomi is safer when users understand
what it can and cannot guarantee today.

## 1) Hard guarantees (current)

- Requests routed through Tsukuyomi are classified and gated by deterministic
  controls (for example: Knee regex blocks, Gary validation rules).
- High-risk flows can be escalated to human approval (Mouth).
- Decision and audit artifacts are persisted for review.

## 2) Non-guarantees (important)

- **No universal prevention of all harmful actions.** Unknown patterns still
  exist; safety is improved, not mathematically complete.
- **No protection for traffic that bypasses the interceptor.** If an agent can
  call upstream models directly, Tsukuyomi cannot enforce policy on that path.
- **No guaranteed correctness of model reasoning.** Tsukuyomi governs allowed
  behavior and checks, not intrinsic model truthfulness.

## 3) Implementation limitations

- **Streaming accounting is partial.** Token/cost accounting is currently
  wired for non-streaming upstream responses.
- **Shoulders precision depends on GitNexus availability/quality.** If MCP or
  index quality degrades, fallback risk is applied conservatively.
- **Mouth webhook is in-process and memory-backed.** Replay prevention is
  process-local; restarting clears nonce memory.
- **NightShift is heuristic.** Proposals are suggestions and can include
  false positives; they must be reviewed by a human.

## 4) Operational limitations

- **Single-process assumptions.** Several safeguards (for example replay
  windows and mismatch counters) are local to one process instance.
- **Policy quality depends on configuration quality.** Unsafe thresholds or
  permissive overrides can weaken protection.
- **Cost control depends on provider usage metadata.** Missing usage fields
  reduce accounting accuracy.

## 5) Explicit non-goals

- Replacing secure SDLC practices, code review, or change-management policy.
- Acting as a full endpoint security product.
- Guaranteeing legal/compliance outcomes without organizational controls.

## 6) Reporting

If a limitation causes unsafe behavior, open an issue (or use `SECURITY.md`
for vulnerability disclosure) with:

- exact prompt/request,
- observed decision path,
- expected behavior,
- relevant artifact references (audit id/log lines).
