# Infinite Tsukuyomi

**A deterministic interceptor-layer that forces safety into any LLM agent, by architecture rather than by prompting.**

[![License: Apache-2.0](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](LICENSE)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Code coverage](https://img.shields.io/badge/coverage-%E2%89%A590%25-brightgreen.svg)](#testing)
[![Status](https://img.shields.io/badge/status-v1.0-green.svg)](CHANGELOG.md)

> *"Current LLM agents are disembodied intelligence — brilliant at reasoning, structurally lacking impulse control. Tsukuyomi gives them a nervous system they cannot bypass."* — Rob de Vet, Anatomic AI Manifesto (2026)

---

## The problem in one paragraph

Autonomous LLM agents fail in four predictable ways: they hallucinate success while files remain unchanged; they burn through budgets in runaway loops; they edit files without understanding blast radius; and they produce ~32% malformed tool invocations on open-weight models. The industry response is *soft prompting* — whispering "please be careful" to a hurricane. Tsukuyomi rejects that paradigm entirely. Safety must be enforced by architecture, not requested by text.

## What Tsukuyomi is

Tsukuyomi is a **transparent interceptor** that sits between any LLM agent and its backing model API. By configuring the agent's `ANTHROPIC_BASE_URL` or `OPENAI_BASE_URL` environment variable to point at Tsukuyomi, every inference request — prompt, tool call, streamed response — passes through a deterministic decision pipeline before reaching the actual model provider. The agent cannot bypass Tsukuyomi because the network path is the only path; Tsukuyomi is not a library the agent chooses to call, it is the address where the agent's model lives.

Inside that pipeline, eight organs enforce the **Head-Shoulders-Knees-and-Toes principle**: four binary gates (impulse control, structural awareness, reflexive brake, resource grounding) and four continuous senses (ambiguity filter, post-action verifier, anomaly detector, human bridge). Together with two protocols — **Protocol Gary** (forced self-audit) and **NightShift** (offline learning from own logs) — and the **Infinite Tsukuyomi sandbox** (mandatory simulation before execution), the system produces an agent that has already failed every possible way in a harmless illusion before it is allowed to act on reality.

## What Tsukuyomi is not

- Not a prompt template or system message (those are bypassable).
- Not a hook integration for Claude Code, Cursor, or any specific agent (hooks are cooperative; Tsukuyomi is coercive).
- Not a wrapper library the agent imports (the agent does not know Tsukuyomi exists).
- Not a memory system for the agent itself (agents like Hermes have their own memory; Tsukuyomi has its *own* memory, about *its own work*).
- Not a reasoning model or fine-tuned LLM (Tsukuyomi does not change what the model *thinks*; it changes what the model is *allowed to do*).

## Quickstart (90 seconds)

```bash
# 1. Install
pip install tsukuyomi

# 2. Start the interceptor
tsukuyomi start --port 9999

# 3. Point your agent at it (Claude Code example)
export ANTHROPIC_BASE_URL=http://localhost:9999
claude-code "refactor the auth module"

# Every request the agent makes now flows through Tsukuyomi:
#   - classified by risk tier
#   - audited by Protocol Gary if high-risk
#   - blast-radius-analyzed via GitNexus
#   - simulated in a Tsukuyomi sandbox before real execution
#   - verified post-action by the Eyes
#   - logged into Tsukuyomi's own anatomic memory
```

That is the entire integration. One environment variable. The agent is now coerced into safe behavior at every step, and it does not know Tsukuyomi is there.

## Agent-agnostic by design

Tsukuyomi speaks the OpenAI and Anthropic HTTP APIs. Any agent that uses these APIs — which is effectively every serious agent framework in 2026 — works with Tsukuyomi without modification:

| Agent | Integration |
| --- | --- |
| Claude Code (Anthropic) | `export ANTHROPIC_BASE_URL=http://localhost:9999` |
| Hermes Agent (Nous Research) | `hermes config set api.base_url http://localhost:9999` |
| Cursor | Point "Custom API endpoint" at Tsukuyomi |
| OpenAI CLI | `export OPENAI_BASE_URL=http://localhost:9999` |
| LangChain / LlamaIndex | Set base URL on any OpenAI-compatible client |
| Custom agent | Use the OpenAI or Anthropic Python SDK with a `base_url` argument |

See `examples/` for runnable demonstrations with each.

## Research foundation

Tsukuyomi is not an invention from first principles; it is the integration of four established research traditions into a previously-unexplored combination:

- **Subsumption architecture** (Brooks, 1986) — layered control where reflexes override deliberation.
- **Dual-process theory** (Kahneman, 2011) — forced System 2 engagement for high-stakes decisions.
- **Cybernetics** (Wiener, 1948) — feedback loops between perception and action.
- **Embodied world models** (LeCun, 2022) — mandatory simulation before real execution.

The full theoretical foundation is laid out in `docs/research/PAPER.md`, which reads as a conference-submittable paper with bibliography of 47 sources. The architecture decision records in `docs/adr/` document every non-trivial choice and the alternatives considered.

## Key differentiators (versus adjacent tools)

| Tool | What it does | What it does not do |
| --- | --- | --- |
| **Guardrails AI** | Output validation against schemas | No interception of tool calls, no sandbox, no blast radius |
| **NeMo Guardrails (NVIDIA)** | Rule-based dialog flow control | Conversational rails only; no filesystem/execution enforcement |
| **LangGraph interrupts** | Human-in-the-loop at graph nodes | Requires agent to be built in LangGraph; cooperative not coercive |
| **Semantic Router** | Fast intent classification | Routing only; no enforcement |
| **Claude Code hooks** | PreToolUse / PostToolUse callbacks | Agent-specific; bypassable; often no-op in practice |
| **Tsukuyomi** | **Coercive interceptor at API layer with full organ anatomy** | **Works for every agent; cannot be bypassed; simulates before executing** |

## Repository layout

```
tsukuyomi/
├── README.md                      (this document)
├── LICENSE                        Apache-2.0
├── CITATION.cff                   How to cite this work academically
├── CHANGELOG.md                   Semantic versioned change log
├── CONTRIBUTING.md                How to contribute
├── CODE_OF_CONDUCT.md             Community standards
├── SECURITY.md                    Vulnerability reporting
├── pyproject.toml                 Package metadata + dependencies
├── mkdocs.yml                     Documentation site config
│
├── docs/
│   ├── architecture/              System architecture documents
│   │   ├── 01_overview.md
│   │   ├── 02_interceptor.md
│   │   ├── 03_organs.md
│   │   ├── 04_protocols.md
│   │   ├── 05_memory.md
│   │   └── 06_observability.md
│   ├── research/
│   │   ├── PAPER.md               Full academic paper (60+ pages)
│   │   ├── bibliography.bib
│   │   └── related_work.md
│   ├── guides/
│   │   ├── installation.md
│   │   ├── integrating_claude_code.md
│   │   ├── integrating_hermes.md
│   │   ├── integrating_cursor.md
│   │   ├── integrating_custom.md
│   │   ├── configuration.md
│   │   ├── operations.md
│   │   └── troubleshooting.md
│   ├── adr/                       Architecture Decision Records
│   │   ├── 0001_interceptor_via_reverse_proxy.md
│   │   ├── 0002_memory_backend.md
│   │   ├── 0003_sandbox_isolation_strategy.md
│   │   ├── 0004_protocol_gary_design.md
│   │   ├── 0005_agent_agnostic_api_surface.md
│   │   ├── 0006_event_bus_choice.md
│   │   ├── 0007_configuration_schema.md
│   │   └── 0008_observability_strategy.md
│   └── diagrams/
│       └── *.mmd                  Mermaid source for diagrams
│
├── src/tsukuyomi/                 Production source code
│   ├── core/                      Arbiter, event bus, configuration
│   ├── interceptor/               Reverse proxy (Anthropic + OpenAI APIs)
│   ├── organs/                    Skin, Shoulders, Knee, Toe, Ears, Eyes, Nose, Mouth
│   ├── protocols/                 Protocol Gary, NightShift
│   ├── memory/                    Anatomic memory (SQLite + FTS5)
│   ├── observability/             Structured logging, metrics, tracing
│   └── adapters/                  Agent-specific shims (Claude Code, Hermes, ...)
│
├── examples/                      Runnable demonstrations
│   ├── 01_claude_code_safe_refactor/
│   ├── 02_hermes_safe_migration/
│   ├── 03_cursor_with_tsukuyomi/
│   ├── 04_custom_agent_openai_sdk/
│   └── 05_gary_blocking_destructive_plan/
│
├── tests/
│   ├── unit/                      Per-module unit tests
│   ├── integration/               Multi-organ scenarios
│   └── acceptance/                Full end-to-end release gates
│
├── scripts/
│   ├── nightshift.py              Cron-compatible log analyzer
│   └── release.sh                 Tag, build, publish
│
├── config/
│   ├── corelaw.example.json       Annotated example configuration
│   └── agents/                    Per-agent integration profiles
│       ├── claude_code.json
│       ├── hermes.json
│       └── cursor.json
│
└── .github/workflows/
    ├── ci.yml                     pytest + mypy + ruff on every PR
    ├── release.yml                Automated PyPI publish on tag
    └── docs.yml                   mkdocs deploy to GitHub Pages
```

## Documentation map

**Start here, in order, depending on who you are:**

### If you are evaluating whether Tsukuyomi is right for you
1. This README
2. `docs/research/PAPER.md` (sections 1–3: problem, thesis, related work)
3. `docs/architecture/01_overview.md`
4. `examples/01_claude_code_safe_refactor/README.md` (runnable proof)

### If you are integrating Tsukuyomi into your agent
1. `docs/guides/installation.md`
2. The integration guide for your specific agent (`docs/guides/integrating_*.md`)
3. `docs/guides/configuration.md`
4. `config/corelaw.example.json`

### If you are operating Tsukuyomi in production
1. `docs/guides/operations.md`
2. `docs/guides/troubleshooting.md`
3. `docs/architecture/06_observability.md`

### If you are contributing to Tsukuyomi
1. `CONTRIBUTING.md`
2. `docs/adr/` (read all of them; do not propose changes that conflict with ratified decisions)
3. `docs/architecture/` (all six documents)
4. The relevant `src/tsukuyomi/<module>/` with its tests

### If you are reviewing this academically
1. `docs/research/PAPER.md` (full paper)
2. `docs/research/bibliography.bib`
3. `CITATION.cff`
4. The ADRs as evidence of principled design decisions

## Versioning and release

Tsukuyomi follows [Semantic Versioning 2.0](https://semver.org/). The public API surface consists of:

- The HTTP interface of the interceptor (OpenAI and Anthropic compatibility).
- The `corelaw.json` schema.
- The Python library entry points (`tsukuyomi.start`, `tsukuyomi.Arbiter`, organ interfaces).

Internal module layouts are not part of the public surface and may reorganize between minor versions.

**v1.0.0** is the first release intended for public use. v0.0 was a reflex-layer proof-of-concept that validated the core hypothesis (knee, toe, eyes, nose organs) on one specific agent. v1.0 generalizes that proof into an agent-agnostic interceptor with the full organ anatomy and both protocols.

## Citing this work

If you use Tsukuyomi in academic work, please cite as described in `CITATION.cff`:

> de Vet, Rob. (2026). *Anatomic AI in Infinite Tsukuyomi: An Interceptor Architecture for Deterministic Safety in Large Language Model Agents.* Version 1.0. https://github.com/robdevet/tsukuyomi

## License

Apache License 2.0. See `LICENSE`. This license is compatible with the dependencies Tsukuyomi builds on (GitNexus, the MCP Python SDK, FastAPI, httpx), and contains the patent grant clause that serious enterprise adopters require.

## Author

Rob de Vet (2026). The original conception, the "Head, Shoulders, Knees and Toes" principle, the Protocol Gary design, and the Infinite Tsukuyomi metaphor are all due to the author. Implementation was assisted by Claude (Anthropic). Full acknowledgments in `docs/research/PAPER.md`.

---

*Build the illusion. Master reality.*
