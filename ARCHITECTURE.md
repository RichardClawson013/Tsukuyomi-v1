# Tsukuyomi architecture (quick map)

If you want the full technical deep dive, start at:

- `docs/architecture/01_overview.md`

If you want the short map first, this file is it.

## Request path

1. Agent sends OpenAI/Anthropic-style request to interceptor.
2. Request is normalized into a canonical internal format.
3. Arbiter runs deterministic gates + protocol checks.
4. If request is permitted, it is forwarded upstream.
5. Response usage/cost/audit data are persisted and observed.

## Components and where they live

- Interceptor (HTTP proxy): `src/tsukuyomi/interceptor/`
- Arbiter (orchestration): `src/tsukuyomi/core/arbiter.py`
- Organs (gates/signals): `src/tsukuyomi/organs/`
- Protocols (Gary/NightShift): `src/tsukuyomi/protocols/`
- Memory backend (SQLite): `src/tsukuyomi/memory/`
- Config schema + loading: `src/tsukuyomi/core/config.py`
- Tests: `tests/`

## Organs in one line each

- Skin: risk-tier classification
- Ears: ambiguity detection
- Shoulders: blast-radius analysis
- Knee: deterministic hard blocks
- Toe: budget zoning / spend controls
- Eyes: expected vs actual action checks
- Nose: anomaly signal tracking
- Mouth: human approval gate

## Protocols in one line each

- Gary: forced self-audit on higher-risk plans
- NightShift: offline heuristic mining + proposal output

## Builder entry points (good places to improve)

1. Streaming accounting parity vs non-stream flows.
2. Replay guard persistence beyond process lifetime.
3. Shoulders quality when external code intelligence is degraded.
4. Expanded adversarial and long-horizon workflow tests.

## Before you start coding

1. Read `KNOWN_LIMITATIONS.md`.
2. Read `CONTRIBUTING.md`.
3. Open or pick an issue before large changes.
4. Keep PRs small and focused.
