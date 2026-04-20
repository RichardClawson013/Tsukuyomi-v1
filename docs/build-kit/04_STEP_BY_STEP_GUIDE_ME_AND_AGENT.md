# Step-by-Step Guide: You + Agent Working Together

This is the practical execution sequence you can run repeatedly.

## Ground rules
- Work in small PR slices.
- Every PR must include tests for behavior changed.
- Keep a `KNOWN_LIMITATIONS.md` updated in public.

## Step 1: Establish truth baseline
You ask agent:
"Create a failing test that proves Gary still uses stub answers and escalates by default. Do not change behavior yet."

Expected result:
- Test demonstrates current limitation clearly.

## Step 2: Implement Gary real executor
You ask agent:
"Implement AuditExecutor abstraction and one real provider-backed executor. Keep validator unchanged. Add unit tests for pass/escalate/error."

Expected result:
- Gary can pass with concrete answers, escalate with weak answers.

## Step 3: Wire cost and timeout safety
You ask agent:
"Add hard timeout and max audit cost enforcement to Gary executor path with tests for both limits."

Expected result:
- no runaway audit loops.

## Step 4: Shoulders real integration
You ask agent:
"Replace Shoulders stub MCP path with real client calls and tests for unavailable/available modes."

Expected result:
- blast radius decisions grounded in code graph data.

## Step 5: Mouth webhook mode
You ask agent:
"Implement webhook approval mode with HMAC validation and replay protection. Keep CLI mode intact. Add tests."

Expected result:
- remote approvals possible for real operations.

## Step 6: Toe actual accounting
You ask agent:
"Extract token usage from upstream responses and call Toe.record_actual. Add integration tests for zone transitions."

Expected result:
- budget zones reflect real spend, not static estimates.

## Step 7: Eyes and Nose event plumbing
You ask agent:
"Wire Nose observers to tool/command/error signals and integrate Eyes verification in post-write flow. Add integration tests."

Expected result:
- anomaly and mismatch detection become operational.

## Step 8: NightShift useful output
You ask agent:
"Implement 3 NightShift heuristics that currently return empty lists. Add tests and markdown proposal fixtures."

Expected result:
- nightly run yields actionable recommendations.

## Step 9: Public hardening docs
You ask agent:
"Create threat model, security assumptions, and known limitations docs. Include explicit non-goals and failure modes."

Expected result:
- claims and limitations are transparent.

## Step 10: Public demo and benchmark harness
You ask agent:
"Create reproducible demo scripts for Tier1, Gary escalation, Knee block, and sandbox mismatch. Include expected outputs."

Expected result:
- external users can verify claims quickly.

## Review loop after each step
For each PR:
1. run tests,
2. run one demo command,
3. update docs,
4. merge only when behavior is reproducible.
