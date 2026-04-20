# Related Work

This document amplifies §3.5 of `PAPER.md` with deeper comparisons to the closest adjacent projects.

## Industry guardrail systems

### Guardrails AI

Guardrails AI specifies a domain-specific language (RAIL) for output validation. Strengths: well-thought-out validator catalog (PII detection, JSON-schema, factual consistency), composable with any LLM call. Limitations relative to Tsukuyomi: operates on outputs, not on tool calls; does not interpose at the API layer; no notion of blast radius, sandbox, or budget. Composability: Tsukuyomi's Ears or Eyes could call Guardrails validators for specific checks. We do not duplicate Guardrails' validator library.

### NeMo Guardrails (NVIDIA)

NeMo Guardrails uses Colang, a DSL for conversational rails. Strengths: very well-suited to chatbot-style dialog flows with constrained transitions. Limitations: not designed for code-execution agents; no integration with filesystem or budget control. Different problem domain.

### LangGraph

LangGraph is a framework for graph-based agent construction with built-in human-in-the-loop interruption nodes. Strengths: explicit graph topology makes intervention points discoverable. Limitations: cooperative (the agent must be built in LangGraph; an agent that bypasses the graph bypasses the safety); agent-author-controlled.

### Semantic Router

Fast embedding-based intent classification. Useful in the Skin layer for tier classification when the deterministic rule set is insufficient. We expect community contributions to wire Semantic Router into Tsukuyomi as a Skin classifier alternative.

### Anthropic's Claude Code Hooks

The closest existing system to part of Tsukuyomi's functionality. Strengths: official, well-integrated. Limitations covered in §3.5 and ADR 0001: agent-specific, cooperative, fragile. The author's experience maintaining hooks in v0.0 motivated the move to interceptor-at-API-layer.

## Academic safety/alignment work

### Constitutional AI (Anthropic)

CAI trains models to internalize a set of principles. Improves baseline safety probabilistically. Tsukuyomi composes with CAI-trained models: a CAI-trained model behind Tsukuyomi is safer than either alone, because CAI raises the *baseline* probability of safe behavior while Tsukuyomi *enforces* invariants regardless of probability.

### RLHF (Christiano et al., Bai et al.)

Reinforcement Learning from Human Feedback. Same compositional relationship as CAI: probabilistic improvement of model behavior; does not provide enforcement.

### LeCun's Objective-Driven AI / JEPA

LeCun's program articulates the world-model gap that the Infinite Tsukuyomi sandbox addresses. We adopt LeCun's diagnosis (autoregressive models lack world models) while taking a different remedy (provide world models externally via sandbox simulation).

## Memory systems

### MemGPT / Letta

OS-inspired tiered memory for agents. *Agent-side* memory: helps the agent be smarter about what to remember from its own task history. Different responsibility from Tsukuyomi's anatomic memory (which is about Tsukuyomi's own decisions, not the agent's task content). v1.1 will add Letta as an optional integration for users who want their agents to have richer memory; Tsukuyomi's anatomic memory remains separate.

### Graphiti

Bi-temporal knowledge graph for agent memory. Same agent-side scope as Letta. Considered for Tsukuyomi's anatomic memory and rejected (ADR 0002): the entity-graph features are unused for audit-log telemetry.

### GBrain

Personal knowledge brain with hybrid search (Postgres + pgvector + tsvector + RRF fusion). Excellent for curated personal knowledge. Considered for anatomic memory and rejected for v1.0 because of the Postgres operational dependency (ADR 0002). Pluggable as an alternative backend in v1.1.

## Sandboxing

### Microsandbox

The v1.1 migration target. Apache-2.0, libkrun-based microVM with Python SDK. The right project to standardize on once it stabilizes (currently v0.x).

### Docker / Docker Sandboxes

Container isolation. Subject to container-escape CVEs. Rejected as v1.1 target in favor of microVM (ADR 0003).

### Penligent four-boundary research

Establishes the conceptual framework for sandbox isolation in agentic contexts: filesystem, process, network, kernel. Tsukuyomi's hardened-worktree implementation maps onto this framework explicitly (`docs/research/PAPER.md` §5.3).

## Tool-call standardization

### Model Context Protocol (MCP)

Standardized JSON-RPC over stdio for LLM tool integration. Complementary to Tsukuyomi: the Shoulders organ uses MCP to talk to GitNexus. We do not depend on MCP for our interception mechanism (which is HTTP-layer).

### Outlines / structured generation (Willard & Louf)

Constrained decoding to guarantee tool-call schema validity. A potential v1.x integration in the Skin/Ears organ for upstream backends that don't natively constrain. Not in v1.0.

## Where Tsukuyomi is novel

To the author's knowledge as of April 2026, no prior public project combines all of the following:

1. Deterministic enforcement at the LLM-API HTTP boundary.
2. Agent-agnostic via wire-protocol compatibility (not vendor-specific).
3. Integration of code-intelligence (blast-radius) into the safety pipeline.
4. Mandatory pre-execution simulation in a sandbox with quantitative match-score criteria.
5. Forced-audit protocol with deterministic validation rules.
6. Self-observing offline-learning loop (NightShift) with human-in-the-loop ratification.
7. Open-source, Apache-2.0-licensed, reference-quality implementation.

Each individual component has prior art; the integration is, to our knowledge, novel.
