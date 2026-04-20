# ADR 0007: corelaw.json — Single-File, Pydantic-Validated, Hand-Editable Configuration

| Field | Value |
| --- | --- |
| **Status** | Accepted |
| **Date** | 2026-04-19 |

## Context

Tsukuyomi has many configurable knobs (per-organ thresholds, pricing tables, Gary's question set, sandbox parameters, retention policies). Configuration design choices include:

1. Many small files vs. one large file.
2. JSON vs. YAML vs. TOML vs. Python.
3. Pydantic-validated vs. duck-typed.
4. Hand-editable vs. UI-only vs. policy-as-code (Rego/CEL).

## Decision

**Single `corelaw.json` file**, **JSON format**, **Pydantic-validated on load**, **hand-editable**.

Long sub-tables (Knee patterns, Gary evasion phrases, model pricing) are referenced by path from the main file:

```json
{
  "organs": {
    "knee": {
      "blocked_patterns_reference": "config/knee_patterns.json"
    }
  }
}
```

This keeps the main file legible and the sub-files maintainable.

## Rationale

### Why a single main file

A safety system's configuration *is* the safety system, in a sense. Distributing it across many files makes review hard. One file (with referenced sub-tables) gives reviewers one place to look first.

### Why JSON

- Universal parser availability (Python stdlib).
- Strict syntax (no YAML-indentation ambiguity, no TOML date-format quirks).
- Diff-friendly.
- Tooling: jq, JSON Schema validation, IDE completion.

YAML rejected because indentation-driven syntax has bitten too many config-as-code projects (see the `norway problem`). TOML rejected because nested structures become awkward.

### Why Pydantic-validated

Loose configuration produces silent misconfiguration ("typo'd a key, defaults silently apply"). Pydantic on load means a wrong key fails Tsukuyomi startup with a clear error.

### Why hand-editable (and why not policy-as-code in v1.0)

Hand-editable JSON is what most users will use most of the time. Policy-as-code (Rego, CEL) is appropriate for enterprise scenarios with policy review processes, and is a v2.0 deliverable. v1.0 picks the lower-friction option.

## Consequences

**Positive**: single source of truth; validated on load; diff-friendly; works in every editor.

**Negative**: very large policies become hard to navigate (mitigated by referenced sub-files). Policy-as-code use cases require Rego/CEL adapters in v2.0.

## Schema versioning

`corelaw.json` includes `"schema_version": 1`. Migrations between schema versions are handled by `tsukuyomi config migrate`.
