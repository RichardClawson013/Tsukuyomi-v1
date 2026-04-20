# Contributing to Tsukuyomi

Thank you for your interest. This project accepts contributions under the Apache License 2.0.

## Before you contribute

Read, in order:
1. `README.md`
2. `docs/research/PAPER.md`
3. All of `docs/adr/` — the architectural commitments are ratified here, and contributions that conflict with them require an ADR amendment rather than a PR-only change.

## What we accept readily

- Bug fixes with a corresponding test.
- New Knee blocklist patterns (additions) with a short rationale.
- New NightShift heuristics.
- Additional agent integration guides.
- Documentation improvements.
- New examples.
- CI/test infrastructure improvements.
- Coverage improvements.

## What requires discussion before PR

- Changes to any of the eight organs' public interfaces.
- Changes to Protocol Gary's validation rules.
- Changes to the sandbox isolation model (see ADR 0003).
- Changes to the memory backend (see ADR 0002).
- Changes to the observability surface (see ADR 0008).
- Anything that weakens a safety invariant.

Open an issue labeled "design-discussion" first. A ratified ADR addition or amendment is expected before the code PR.

## What we will not accept

- Bypass mechanisms that let agents reach the model directly while Tsukuyomi is running (ADR 0001).
- Removal or weakening of the Knee blocklist without explicit evidence.
- Agent-specific coupling that breaks agent-agnosticism (ADR 0005).
- Auto-applying NightShift proposals (ADR 0004 §NightShift).

## Code standards

- Python 3.11+.
- `ruff check .` must pass.
- `mypy --strict src/tsukuyomi` must pass.
- `pytest --cov=src/tsukuyomi` must report ≥90% coverage.
- No new dependencies without justification in the PR description.

## Commit messages

Short imperative subject (50 chars), blank line, wrapped body. Reference ADRs and issues.

Example:
```
knee: add kubectl delete --all pattern

Users hit this pattern 23 times last quarter; the variant
without `--all` is intentional. See NightShift proposal
2026-03-12-kubectl.md for evidence.

Fixes #47.
```

## Testing

```bash
pytest tests/unit/                 # fast
pytest tests/integration/          # slower; real SQLite, real sandbox
pytest tests/acceptance/           # release gates
pytest --cov=src/tsukuyomi tests/  # full with coverage
```

## Reporting security issues

See `SECURITY.md`. Do not open public GitHub issues for security problems.
