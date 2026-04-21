# Launch checklist (builder-ready)

Use this before public posting so feedback converts into issues and PRs, not noise.

## Repository readiness

- [ ] `README.md` is honest about current status (not overclaiming).
- [ ] `KNOWN_LIMITATIONS.md` reflects current branch truth.
- [ ] `CONTRIBUTING.md` exists and tells people how to help.
- [ ] `ARCHITECTURE.md` exists with quick entry points.
- [ ] Bug template exists at `.github/ISSUE_TEMPLATE/bug_report.yml`.
- [ ] At least 5 issues are labeled `good first issue` or `help wanted`.

## Validation readiness

- [ ] Unit tests pass (`pytest tests/unit/`).
- [ ] Integration tests pass (`pytest tests/integration/`).
- [ ] Acceptance tests pass (`pytest tests/acceptance/`).
- [ ] One-command gate runs (`scripts/acceptance_gate.sh`).
- [ ] Benchmark validation runner executes (`scripts/benchmark_validation_runner.sh`).

## Posting readiness

- [ ] You can answer: "What is unfinished?" in 2-3 lines.
- [ ] You can answer: "Where should builders start?" in 2-3 lines.
- [ ] You can answer: "What kind of bug report do you want?" in 2-3 lines.

## Response readiness (after posting)

- [ ] First response to good-faith comments within 24h.
- [ ] Every actionable report is converted into an issue.
- [ ] Every merged fix is referenced in a public update thread.
- [ ] Weekly recap posted with: bugs found, bugs fixed, open asks.

## Hard rule

If this checklist is not mostly green, delay posting and fix the repo first.
