# Changelog

What got added and changed in each version.

## 1.0.0 — April 2026

First version I'm releasing publicly.

What's in it:

- A reverse-proxy interceptor that speaks the OpenAI and Anthropic HTTP formats, so any agent using those formats can point at it.
- Eight "organs": Skin, Ears, Shoulders, Knee, Toe, Eyes, Nose, Mouth. Each does one thing. See `docs/architecture/03_organs.md` for what each does.
- Two protocols: Protocol Gary (forces the agent to audit its own plan) and NightShift (looks at logs and suggests config changes, never applies them).
- The Infinite Tsukuyomi sandbox — runs an agent plan in a git-worktree clone before letting it touch real files.
- A small database layer on SQLite + FTS5 for Tsukuyomi's own audit trail.
- Logging that tries not to leak credentials.
- A command-line tool: `tsukuyomi start`, `init`, `version`, `config validate`, `memory stats`, `nightshift`.
- Documentation in `docs/architecture/`, eight Architecture Decision Records in `docs/adr/`, five examples in `examples/`.
- A research paper in `docs/research/PAPER.md` with a 90-source bibliography.
- 31 tests across unit, integration, and acceptance that pass on my machine.
- A CI pipeline on GitHub Actions that tries to run pytest, mypy, and ruff.

What's not finished:

- The part of Protocol Gary that calls a second LLM to answer the five audit questions is a stub. The validation logic around it works, but someone has to wire the actual model call. See `docs/research/PAPER.md` section 7.2.
- The GitNexus blast-radius client is also stubbed. It falls back to "UNKNOWN," which the rest of the system treats as high risk. Safe, but you're not getting real blast-radius numbers.
- The sandbox uses a hardened git worktree, not a microVM. It's good enough for one trusted user on their own machine. It is not good enough for multi-tenant or untrusted-input scenarios. See `docs/adr/0003_sandbox_isolation_strategy.md`.

## Before 1.0.0

Before I called this v1.0, I spent months on proof-of-concept versions that only worked with one specific agent (Claude Code) and only had the reflex layer (Knee, Toe, Eyes, Nose). Those weren't released publicly. They existed to convince me that the basic idea wasn't crazy. The 1.0 is the generalized version — agent-agnostic, all eight organs, both protocols, the sandbox, the memory layer.

---

Missing something that should be in here? Open an issue.

rob@droogdoc.info · umakemedo@proton.me
