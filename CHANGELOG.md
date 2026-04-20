# Changelog

All notable changes to Tsukuyomi are documented here. Format based on
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/).
Versioning follows [Semantic Versioning 2.0](https://semver.org/).

## [1.0.0] — 2026-04-20

### Added
- First public release.
- Reverse-proxy interceptor supporting OpenAI Chat Completions and Anthropic Messages wire formats.
- Eight organs: Skin, Ears, Shoulders, Knee, Toe, Eyes, Nose, Mouth.
- Two protocols: Protocol Gary (forced self-audit), NightShift (offline learning).
- Infinite Tsukuyomi sandbox with git-worktree backend and four-layer hardening.
- Anatomic memory backed by SQLite + FTS5.
- Structured JSON logging with mandatory key scrubbing.
- CLI: `tsukuyomi start`, `init`, `version`, `config validate`, `memory stats`, `nightshift`.
- Full architecture documentation (`docs/architecture/01-06`).
- Academic paper (`docs/research/PAPER.md`) with 47-source bibliography.
- 8 Architecture Decision Records (`docs/adr/`).
- Integration guides for Claude Code, Hermes, Cursor, custom agents.
- Operations and troubleshooting guides.
- 5 runnable examples.
- Unit, integration, and acceptance test suites; coverage target ≥90%.
- CI pipeline (pytest, mypy, ruff).

### Known limitations
- Sandbox uses hardened git worktree (not microVM); adequate for single-trusted-user local deployment. See ADR 0003.
- Protocol Gary's audit-LLM executor ships as a stub; users must wire to configured upstream.
- Multi-tenant deployment is out of scope; reserved for v2.0.

## [0.0.x] — 2026-01 through 2026-03 (pre-release)
Reflex-layer proof-of-concept validated Knee, Toe, Eyes, Nose on a single agent. Not publicly released.
