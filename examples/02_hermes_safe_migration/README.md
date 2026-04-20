# Example 02 — Hermes Agent Running a Database Migration

Hermes Agent attempting a destructive DB migration. Demonstrates how Tsukuyomi
protects against aggressive open-weight agent behavior with tight thresholds.

## Run

```bash
tsukuyomi start --profile config/agents/hermes.json
export OPENAI_BASE_URL=http://localhost:9999
hermes "apply the migration 2026_04_19_drop_legacy_users.sql to the production database"
```

## Expected flow

- **Skin**: Tier 3 (keywords `apply the migration` + `production database`).
- **Shoulders**: flagged HIGH because migration path intersects with schema files.
- **Protocol Gary**: forced audit. Hermes's open-weight model often produces
  shape-valid but content-thin round-1 answers; the deterministic validation
  catches this; round 2 required.
- **Sandbox**: the migration runs against a git-worktree copy of the repo; if
  the resulting diff doesn't match declared `expected_files`, the plan fails.
- **Mouth**: because `production` is in the prompt, CRITICAL approval triggered.
- Only after human approval is the request forwarded to the model.
