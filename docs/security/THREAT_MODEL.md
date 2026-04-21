# Tsukuyomi Threat Model (v1.0 hardening baseline)

This document defines what Tsukuyomi is designed to defend, what it currently
does not defend, and where operational assumptions matter.

## 1) System boundary

Tsukuyomi is an API-layer interceptor between an agent and upstream LLM
providers. Requests pass through:

- Interceptor (OpenAI/Anthropic wire compatibility)
- Arbiter and organs/protocols
- Upstream model providers

Primary protected assets:

- Filesystem and git repository integrity
- Model provider credentials
- Budget and cost controls
- Audit/logging integrity

## 2) Adversary model

We assume adversaries may include:

- Prompt-level adversaries attempting to coerce destructive operations.
- Misaligned or malfunctioning autonomous agent loops.
- Operators with accidental unsafe configuration.
- Network attackers who can tamper with approval callbacks.

We do **not** assume root-level host compromise is preventable by Tsukuyomi.

## 3) Trust assumptions

- Host OS and runtime are not already compromised.
- Upstream model APIs are reachable and correctly authenticated.
- Mouth webhook secret remains secret.
- Optional external systems (e.g., GitNexus MCP) may fail; Tsukuyomi must fail
  conservatively when they do.

## 4) Key threats and controls

### 4.1 Destructive action execution
Threat:
- Agent attempts destructive commands or risky DB/SCM operations.

Controls:
- Skin tiering + Knee deterministic blocklist.
- Gary forced audit for high-risk paths.
- Sandbox simulation and Eyes verification (for write-heavy/high-risk flows).
- Mouth escalation for unresolved risk.

Residual risk:
- Unknown destructive patterns not captured by deterministic rules.

### 4.2 Bypass of control plane
Threat:
- Agent routes around Tsukuyomi directly to provider.

Controls:
- Deployment architecture must force provider traffic through Tsukuyomi endpoint.

Residual risk:
- Misconfiguration can reintroduce bypass paths.

### 4.3 Budget runaway
Threat:
- Looping agents consume excessive tokens/cost.

Controls:
- Toe zone management and downgrade map.
- Post-response accounting from upstream usage payloads.

Residual risk:
- Streaming usage accounting is partial in v1.0; non-stream path is authoritative.

### 4.4 Approval channel tampering/replay
Threat:
- Forged webhook approval responses or replayed approvals.

Controls:
- HMAC signature verification.
- Timestamp skew checks.
- Nonce replay window enforcement.

Residual risk:
- In-memory replay window resets on process restart.

### 4.5 External dependency unavailability (GitNexus etc.)
Threat:
- Loss of external analysis causes blind spots.

Controls:
- Shoulders fallback to conservative `unknown_treated_as` risk.

Residual risk:
- Increased false positives / operator friction.

## 5) Non-goals

- Defending against a fully compromised host.
- Guaranteeing zero false positives.
- Guaranteeing perfect semantic understanding of user intent.

## 6) Security-in-depth recommendations

- Run Tsukuyomi on a dedicated host/container boundary.
- Restrict outbound network where possible.
- Rotate webhook secrets regularly.
- Keep Knee patterns and Gary phrase/risk vocab files reviewed.
- Track known limitations in `KNOWN_LIMITATIONS.md`.

