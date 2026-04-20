# Public Execution Playbook

You said you want to build this in public. This is how to do that without overclaiming.

## 1) Public positioning
Use this framing:
- "Tsukuyomi is a safety interceptor in active hardening."
- Avoid: "complete" or "production ready" until objective criteria pass.

## 2) Public repo hygiene
Add/maintain:
- `SECURITY.md` with disclosure process
- `KNOWN_LIMITATIONS.md`
- `THREAT_MODEL.md`
- `docs/benchmarks/` with reproducible scenarios

## 3) Transparent maturity model
Define levels publicly:
- Level 0: architecture scaffold
- Level 1: deterministic controls validated
- Level 2: real external integrations
- Level 3: operational reliability

Map current state to a level and update after each milestone.

## 4) Community trust mechanics
- Publish failing tests when they reveal real gaps.
- Keep issue labels clear: `security-gap`, `stub`, `needs-test`, `ready-for-review`.
- Never hide known unsafe behavior.

## 5) Demo discipline
Every demo should include:
- prompt input,
- system decision,
- relevant artifact path,
- exact command to reproduce.

## 6) Release gate before claiming "proper build"
Do not claim full readiness until:
- Gary real executor + tests,
- Shoulders real MCP integration + tests,
- Mouth webhook mode + tests,
- Toe accounting wired end-to-end,
- Eyes/Nose wired to runtime events,
- NightShift produces useful proposals,
- observability endpoint and runbook present.
