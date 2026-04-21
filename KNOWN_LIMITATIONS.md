# Known limitations (as of this branch)

Short version: this works, but it's not magic and it's not finished forever.
This file exists so nobody has to guess what is and isn't true today.

## What is true right now

- The pipeline has deterministic gates (Knee regex, Gary validation, budget zones).
- High-risk paths can escalate to a human decision (Mouth).
- Decisions and audit trails are persisted.
- Gary HTTP executor, Shoulders MCP path, webhook signing, and non-stream cost
  accounting are wired on this branch.

## What is still rough

- **Streaming accounting is weaker than non-stream accounting.**
  Non-stream responses now feed Toe directly; stream usage still needs deeper handling.
- **Webhook replay protection is process-local.**
  Nonce memory lives in-process, so restarting resets the replay window.
- **Shoulders quality depends on GitNexus health and index freshness.**
  When external code-intelligence degrades, fallback risk goes conservative.
- **NightShift proposals are heuristics, not ground truth.**
  They are suggestions for humans to review, not auto-applied policy.

## What this project does NOT promise

- It does not make all harmful actions impossible.
- It does not protect traffic that bypasses the interceptor path.
- It does not make model reasoning "correct" by itself.

## Non-goals

- Replacing secure SDLC practices, code review, or change management.
- Acting as a full endpoint security product.
- Guaranteeing compliance outcomes on its own.

## If this limitation list is wrong

Open an issue (or use `SECURITY.md` for sensitive reports) and include:

- exact prompt/request,
- what happened,
- what you expected,
- artifact references (logs, audit id, request id).
