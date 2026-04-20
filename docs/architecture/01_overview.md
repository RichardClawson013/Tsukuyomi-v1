# 01 — Architecture Overview

**Document type:** System-level architecture overview
**Audience:** Engineers and architects evaluating or integrating Tsukuyomi
**Prerequisites:** None
**Reading time:** 20 minutes

---

## 1. What Tsukuyomi is, architecturally

Tsukuyomi is a **reverse-proxy interceptor** that sits between an LLM agent and the LLM provider it talks to. All inference traffic from the agent flows through Tsukuyomi; the agent cannot reach the model without going through Tsukuyomi; the agent does not know Tsukuyomi is there.

```
┌──────────┐         ┌────────────┐         ┌──────────────┐
│  Agent   │────────▶│ Tsukuyomi  │────────▶│ LLM Provider │
│          │   HTTP  │            │  HTTP   │              │
└──────────┘         └────────────┘         └──────────────┘
     ▲                     │
     │                     │
     └─── streaming ◀──────┘
          response
```

The interceptor accepts either the OpenAI Chat Completions wire format or the Anthropic Messages wire format (the two dominant standards as of 2026). It forwards, after processing, to a configurable upstream — Anthropic directly, OpenAI directly, OpenRouter, a local Ollama instance, or any OpenAI- or Anthropic-compatible endpoint.

This deployment topology has one non-negotiable consequence: **there is no path for the agent to reach a model except through Tsukuyomi**. This is the architectural basis of coerciveness — not a social contract with the agent, but a network-topological fact.

## 2. The five-layer architecture

Inside Tsukuyomi, a request flows through five logical layers:

```
┌─────────────────────────────────────────────────────────┐
│ Layer 5  OBSERVABILITY         structured logs,          │
│          (cross-cutting)        metrics, traces           │
├─────────────────────────────────────────────────────────┤
│ Layer 4  MEMORY                anatomic memory            │
│          (persistent)           SQLite + FTS5             │
├─────────────────────────────────────────────────────────┤
│ Layer 3  PROTOCOLS             Protocol Gary              │
│          (cross-organ)          NightShift                │
├─────────────────────────────────────────────────────────┤
│ Layer 2  ORGANS                 Skin  Shoulders  Knee    │
│          (request pipeline)     Toe   Ears  Eyes  Nose   │
│                                  Mouth                    │
├─────────────────────────────────────────────────────────┤
│ Layer 1  INTERCEPTOR            HTTP reverse proxy        │
│          (wire protocol)        OpenAI + Anthropic compat │
└─────────────────────────────────────────────────────────┘
```

### Layer 1 — Interceptor (wire protocol)

Accepts HTTP requests from agents in OpenAI or Anthropic format. Parses them into a canonical internal representation. On the outbound side, serializes back to whichever format the configured upstream expects. Handles streaming in both directions. This layer is **agent- and model-agnostic by construction**: it does not know which agent is calling it (Claude Code, Hermes, Cursor, custom) and it does not know which model will be served (Claude, GPT, Llama, Qwen).

Implementation: `src/tsukuyomi/interceptor/`.

### Layer 2 — Organs (request pipeline)

Eight organs inspect and transform the canonical request. Four are binary gates with unconditional veto power (Skin, Shoulders, Knee, Toe); four are continuous senses that emit signals rather than block (Ears, Eyes, Nose, Mouth). The organs are arranged in a subsumption order: lower organs (reflexes) can override higher organs (deliberation).

Implementation: `src/tsukuyomi/organs/`. Full specification in `03_organs.md`.

### Layer 3 — Protocols (cross-organ orchestration)

Two protocols coordinate multiple organs toward safety goals that no single organ can achieve alone:

- **Protocol Gary** — forces a structured self-audit by the agent before permitting high-risk operations.
- **NightShift** — analyzes Tsukuyomi's own operational history offline and proposes refinements to the configuration.

Implementation: `src/tsukuyomi/protocols/`. Full specification in `04_protocols.md`.

### Layer 4 — Memory (persistent state)

The **anatomic memory** records Tsukuyomi's own operational history: every organ decision, every protocol outcome, every sandbox result, every budget zone transition. It is distinct from (and layered alongside) whatever memory the *agent* itself maintains. An agent like Hermes has its own skills and memory for its own work; Tsukuyomi's memory is about *Tsukuyomi's* work.

Backend: SQLite with FTS5. Full specification in `05_memory.md`. Decision rationale in ADR 0002.

### Layer 5 — Observability (cross-cutting)

Structured JSON logging via `structlog`, with optional OpenTelemetry traces. Every organ decision, every protocol step, every sandbox execution, every anatomic-memory write is observable. This is both operational (debugging, monitoring) and scientific (enabling the empirical studies proposed in the paper).

Implementation: `src/tsukuyomi/observability/`. Full specification in `06_observability.md`.

## 3. The request lifecycle

A canonical Tier-3 (high-risk) request traverses Tsukuyomi as follows. Tier-1 requests skip most of this; the Skin's job is to route the request down the correct path.

```
  ┌─────────────────┐
  │ Agent sends     │
  │ POST /messages  │  (or /v1/chat/completions)
  └────────┬────────┘
           │
  ┌────────▼─────────┐        ┌─────────────────────────┐
  │ Interceptor      │──────▶ │ Parse → canonical form   │
  │ accepts request  │        └─────────────────────────┘
  └────────┬─────────┘
           │
  ┌────────▼────────┐
  │ Skin: Tier 3    │
  └────────┬────────┘
           │
  ┌────────▼────────┐
  │ Ears: clear     │        (if ambiguous → Mouth)
  └────────┬────────┘
           │
  ┌────────▼──────────┐
  │ Shoulders:        │       (GitNexus MCP → blast radius)
  │ blast=HIGH,       │
  │ callers=12        │
  └────────┬──────────┘
           │
  ┌────────▼────────┐
  │ Protocol Gary:  │       (5-question structured audit)
  │ Round 1: fail   │
  │ Round 2: pass   │
  └────────┬────────┘
           │
  ┌────────▼──────────────┐
  │ Infinite Tsukuyomi    │   (git worktree)
  │ sandbox: plan runs,   │   (actual diff vs expected)
  │ match_score = 0.94    │
  └────────┬──────────────┘
           │
  ┌────────▼────────┐
  │ Knee: no dest.  │       (regex blocklist)
  │ patterns        │
  └────────┬────────┘
           │
  ┌────────▼────────┐
  │ Toe: GREEN      │       (budget ok, model ok)
  └────────┬────────┘
           │
  ┌────────▼────────┐
  │ FORWARD to      │──────▶ [Upstream LLM]
  │ upstream        │        
  └────────┬────────┘
           ▲
  ┌────────┴────────┐
  │ Response stream │◀────── [Upstream]
  │ returned to     │
  │ agent           │
  └────────┬────────┘
           │
  ┌────────▼────────────────┐
  │ Eyes: verify file        │    (after agent executes
  │ changes match intent     │     tool calls from response)
  └────────┬────────────────┘
           │
  ┌────────▼────────────┐
  │ Nose: update rolling │
  │ anomaly window       │
  └────────┬────────────┘
           │
  ┌────────▼────────┐
  │ Memory: persist  │
  │ audit record     │
  └─────────────────┘
```

For Tier-1 requests (the common case: *"what does this function do?"*), the Skin routes directly to Toe → forward, with Eyes and Nose observing but not blocking. The heavy machinery activates only where needed.

## 4. Design commitments

Three commitments govern every architectural decision in Tsukuyomi. Changes to the codebase that violate them must be rejected in review.

### Commitment 1 — Coercion, not cooperation

Every safety mechanism in Tsukuyomi must operate regardless of agent cooperation. The agent must not be able to disable safety by misbehaving, by producing malformed output, or by any conversational trick. This is the reason for the interceptor pattern: the network path is not something the agent negotiates. This is the reason Protocol Gary is a *separate* LLM call on Tsukuyomi's side rather than a request inserted into the agent's context (which the agent could ignore). This is the reason the Knee uses regex on the raw command string rather than asking the agent "are you sure?"

### Commitment 2 — Agent-agnostic, model-agnostic, provider-agnostic

Tsukuyomi must work for **any agent** that uses a configurable base URL (which, as of 2026, means effectively every agent). It must work with **any model** accessible through OpenAI- or Anthropic-compatible APIs. It must work with **any provider** — cloud or local, paid or free.

This commitment drives the HTTP-interception design. It forbids building Tsukuyomi as a Claude-Code plugin, a LangChain integration, an Anthropic SDK wrapper, or any other agent-specific or library-specific form.

### Commitment 3 — Determinism in the gates, intelligence in the protocols

The four binary gates (Skin, Shoulders, Knee, Toe) contain no LLM calls. They are deterministic, fast (microsecond to sub-second), and perfectly reproducible. The four senses and the two protocols *may* use LLM calls (Protocol Gary does; the Ears may use a small classifier), but only where the added intelligence justifies the unpredictability cost.

This separation is principled, not aesthetic. The gates are the safety floor; they must be reliable under every condition, including when upstream providers are down, when the network is flaky, when the LLM has a bad day. If the reflex layer depended on LLM behavior, the safety property would become probabilistic — which is exactly what this project exists to replace.

## 5. Deployment configurations

### 5.1 Developer workstation (most common)

Tsukuyomi runs as a foreground process on `localhost:9999`. Configuration is in `~/.config/tsukuyomi/corelaw.json`. The agent (Claude Code, Hermes, Cursor, etc.) points at Tsukuyomi via environment variable. The TUI dashboard is in a separate terminal.

```
┌──────────────────────────────────┐
│  Developer machine (WSL/Linux)   │
│                                  │
│  ┌────────────┐   ┌──────────┐  │
│  │ Claude Code│──▶│Tsukuyomi │──┼──▶ [cloud LLM]
│  │ terminal   │   │ :9999    │  │
│  └────────────┘   └──────────┘  │
│                        │         │
│  ┌──────────────┐      │         │
│  │ TUI dashboard│◀─────┘         │
│  └──────────────┘                │
└──────────────────────────────────┘
```

### 5.2 Shared local service (single user, multiple agents)

Tsukuyomi runs as a systemd service. All agents on the machine are configured to point at it. One anatomic-memory database serves all agents.

### 5.3 Remote/team deployment (future — v2.0 scope)

Not yet supported in v1.0. Multi-tenant isolation, SSO, audit export to SIEM are all planned for v2.0.

## 6. Cross-referenced documents

- Full request-pipeline detail: `02_interceptor.md`
- Per-organ specifications: `03_organs.md`
- Protocol designs: `04_protocols.md`
- Memory schema and retention: `05_memory.md`
- Observability and metrics: `06_observability.md`
- Full theoretical grounding: `../research/PAPER.md`
- Every non-trivial design choice and alternatives considered: `../adr/`
- Visual diagrams: `../diagrams/`

---

*Next: `02_interceptor.md` — the wire protocol and how HTTP interception works in detail.*
