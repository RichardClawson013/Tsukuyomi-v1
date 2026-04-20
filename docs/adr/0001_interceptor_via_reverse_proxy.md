# ADR 0001: Tsukuyomi as a Reverse-Proxy Interceptor at the LLM API Boundary

| Field | Value |
| --- | --- |
| **Status** | Accepted |
| **Date** | 2026-04-19 |
| **Decision-makers** | Rob de Vet |
| **Consulted** | Claude (Anthropic), v0.0 operational experience |
| **Informed** | All future contributors |

## Context

Tsukuyomi must enforce safety on autonomous LLM agents. Several deployment patterns are possible:

1. **Library/SDK**: agent imports `tsukuyomi` and wraps its LLM calls.
2. **Agent-specific plugin/hook**: e.g. Claude Code `PreToolUse`/`PostToolUse`, Cursor extensions, LangGraph interrupts.
3. **Wire-protocol interceptor**: a process between the agent and the LLM provider that the agent's HTTP traffic must pass through.
4. **Model-side enforcement**: a fine-tuned model that internally refuses unsafe behavior.

Each pattern has different coercion guarantees, different agent-coverage, and different operational complexity.

## Decision

We adopt **pattern 3: a reverse-proxy interceptor at the LLM API boundary** (HTTP layer, OpenAI/Anthropic wire protocols). The agent is configured with `ANTHROPIC_BASE_URL` (or `OPENAI_BASE_URL`, etc.) pointing at Tsukuyomi. Every inference request flows through Tsukuyomi before reaching the model provider.

## Rationale

The reverse-proxy pattern is the only pattern that simultaneously satisfies all three of our design commitments (see `docs/architecture/01_overview.md` §4):

1. **Coercion, not cooperation.** The network path is the only path. The agent cannot bypass Tsukuyomi by misbehaving, by ignoring safety calls, or by being misconfigured to skip them — Tsukuyomi *is* the model from the agent's perspective.

2. **Agent-agnostic, model-agnostic, provider-agnostic.** Every modern LLM agent uses HTTP to talk to its model and supports configurable base URLs. One proxy serves Claude Code, Hermes, Cursor, LangChain, OpenAI CLI, custom agents — without per-agent integration code.

3. **Determinism in the gates.** The proxy layer itself contains no LLM; the routing and serialization are deterministic. Intelligence is added selectively in protocols, not in the network path.

## Alternatives considered

### A. Library/SDK

**Rejected** because it assumes agent cooperation. An uncooperative agent — whether buggy, adversarially modified, or accidentally misconfigured — bypasses safety. Empirically, the failure mode of cooperative safety in production is "the engineer turned off the wrapper to debug something and forgot to turn it back on."

### B. Agent-specific plugin/hook

**Rejected** because it solves the problem only for one vendor's agent. A safety property that exists in Claude Code but not in Cursor is not a safety property of LLM agents. Additionally, Anthropic's own Claude Code hooks are documented but empirically fragile across versions; the author maintained hook-based safety in v0.0 and observed silent breakage.

### C. Wire-protocol interceptor

**Selected.** See *Decision* above.

### D. Model-side enforcement

**Rejected as a substitute, accepted as a complement.** A well-aligned model is desirable but provides probabilistic safety. The architectural problem (no proprioception, no resource grounding, no consequence-awareness) is structural and not solved by alignment alone. Tsukuyomi composes with aligned models; it does not replace them.

## Consequences

### Positive

- Single env-var integration story for any agent.
- Agent does not know Tsukuyomi exists; cannot intentionally bypass.
- Wire protocol is stable; safety layer evolves independently of agents.
- Provider-swap (Anthropic ↔ OpenAI ↔ OpenRouter ↔ local) is a config change, not a re-integration.

### Negative

- Latency: 1–5ms HTTP overhead per request, plus organ-pipeline cost. On Tier-3 requests this can be 5–30s; this is by design (high-risk operations should not be fast) but must be communicated.
- Streaming end-to-end correctness adds implementation complexity.
- Two wire formats (OpenAI, Anthropic) must both be supported and kept in sync as the upstream APIs evolve.
- Tsukuyomi becomes a single point of failure: if Tsukuyomi is down, no agent can run. This is a deliberate coupling — safety should not be optional infrastructure that gets disabled "to get work done."

### Mitigations

- The Skin tier classifier (organ §4.1) ensures heavy machinery activates only on high-risk requests.
- Format conversion is an isolated module (`src/tsukuyomi/interceptor/format_adapter.py`) tested against the upstream providers' published examples.
- Tsukuyomi-down behavior: the agent receives connection-refused; this is explicit and observable, unlike silent bypass.

## Compliance with this ADR

PRs that propose any of the following must reference and amend this ADR:

- Tsukuyomi as an importable library that the agent calls directly (rather than via HTTP).
- Agent-specific integration paths bypassing the HTTP layer.
- "Off mode" or `--disable-safety` flags that allow direct agent→provider connection.

These are explicitly forbidden by this ADR's Decision.
