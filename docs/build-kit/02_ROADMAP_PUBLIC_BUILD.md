# Public Build Roadmap (Execution-Oriented)

This roadmap is structured as technical milestones, not calendar promises.

## Milestone 0: Baseline hard truth
Goal: lock current behavior and gaps so future claims are verifiable.

Deliverables:
- [ ] `docs/build-kit/01_REPOSITORY_REALITY_CHECK.md` kept current.
- [ ] smoke script that proves: tier3 -> Gary -> Mouth escalation path.
- [ ] acceptance test matrix document.

Exit criteria:
- You can demonstrate current behavior live without editing code mid-demo.

## Milestone 1: Gary becomes real
Goal: replace stubbed audit executor with real provider-backed implementation.

Deliverables:
- [ ] pluggable audit executor interface.
- [ ] provider adapters (Anthropic/OpenAI/OpenRouter config path).
- [ ] strict timeout/retry/cost caps.
- [ ] tests: pass/fail/escalate plus provider failure modes.

Exit criteria:
- Gary no longer returns empty answers in normal operation.

## Milestone 2: Shoulders productionization
Goal: replace placeholder target extraction + MCP stub path.

Deliverables:
- [ ] explicit target extraction from tool args + diff context.
- [ ] actual GitNexus MCP client integration.
- [ ] fallback strategy documented and tested.

Exit criteria:
- Blast radius reflects real code intelligence in at least one reference repo.

## Milestone 3: Mouth remote approvals + ops safety
Goal: remove local-only bottleneck.

Deliverables:
- [ ] webhook approval backend.
- [ ] signature verification and replay protection.
- [ ] operator UI or CLI helper for approvals.

Exit criteria:
- escalation can be approved/denied remotely with audit logging.

## Milestone 4: End-to-end accounting and observability
Goal: make cost/latency/decision measurable.

Deliverables:
- [ ] hook Toe `record_actual` in forward-response path.
- [ ] per-request usage extraction from upstream responses.
- [ ] metrics endpoint with decision counters and organ latencies.

Exit criteria:
- budget zones change based on real traffic.

## Milestone 5: Sandbox and Eyes hardening
Goal: reduce false confidence in execution verification.

Deliverables:
- [ ] stronger sandbox isolation strategy and documented threat model.
- [ ] robust expected-vs-actual verification pipeline.
- [ ] repeated mismatch handling and escalation policy tests.

Exit criteria:
- destructive dry-runs are reproducible and auditable.

## Milestone 6: NightShift intelligence and release discipline
Goal: make learning loop useful but safe.

Deliverables:
- [ ] implement at least 3 currently-stubbed heuristics.
- [ ] proposal quality scoring.
- [ ] explicit human review workflow.

Exit criteria:
- NightShift outputs actionable proposals in real usage.

## Milestone 7: Public trust packaging
Goal: credibility in open source, not just code.

Deliverables:
- [ ] security policy, disclosure policy, threat model docs.
- [ ] benchmark scenarios + reproducible demos.
- [ ] transparent known limitations page.

Exit criteria:
- outsiders can validate claims independently.
