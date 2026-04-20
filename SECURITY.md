# Security Policy

## Reporting a vulnerability

**Do not open a public GitHub issue for security vulnerabilities.**

Email: `security@tsukuyomi.dev` (or the author directly: `rob@tsukuyomi.dev`).

Include:
- A description of the vulnerability.
- Steps to reproduce.
- Impact assessment.
- Suggested mitigation (if any).

## Response expectations

- Acknowledgment: within 72 hours.
- Initial assessment: within 7 days.
- Fix timeline: depends on severity; we will communicate a target date.

## Scope

In scope for security reports:
- Sandbox-escape vulnerabilities in any backend.
- Bypass of the Knee blocklist.
- Credential leakage through logs or memory.
- Prompt-injection scenarios that subvert Protocol Gary validation.
- Memory-corruption or SQL-injection in the anatomic memory.
- Any path that lets an agent reach a model provider without traversing the Tsukuyomi pipeline.

Out of scope (still useful as issues, not security vulns):
- Performance issues.
- Configuration mistakes that reduce safety (these are user-error, not vulnerabilities).
- Behaviors documented as known limitations in ADRs or PAPER.md §7.2.

## Supply chain

We pin dependencies in `pyproject.toml` and verify with a lockfile. Please report suspicious dependency updates via the same channel.
