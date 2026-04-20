# Anatomic AI in Infinite Tsukuyomi: An Interceptor Architecture for Deterministic Safety in Large Language Model Agents

**Rob de Vet**
Independent Researcher
[rob@tsukuyomi.dev](mailto:rob@tsukuyomi.dev)

**Version 1.0 — April 2026**

---

## Abstract

Autonomous agents built on Large Language Models (LLMs) exhibit a reproducible class of failure modes — hallucinated success, runaway token expenditure, blast-radius ignorance, and malformed tool invocation — that stem from a structural property: they possess cognitive capacity without proprioception, resource grounding, or consequence-awareness. The dominant industry response is *soft prompting*: natural-language requests for cautious behavior, appended to system prompts. This paper argues that soft prompting is architecturally insufficient, and demonstrates a constructive alternative. We present **Anatomic AI in Infinite Tsukuyomi**, a deterministic interceptor layer that sits on the network path between any LLM agent and its backing model API, forcing every inference request through a pipeline of layered safety organs before it can reach the model or produce tool calls. The architecture draws on Brooks' subsumption model (1986), Kahneman's dual-process theory (2011), Wiener's cybernetic feedback (1948), and LeCun's embodied world-model program (2022), integrating them into a single coherent system expressible via the childhood mnemonic *Head, Shoulders, Knees, and Toes*. We describe the eight organs (four binary gates, four continuous senses), two enforcement protocols (Protocol Gary for forced self-audit; NightShift for offline learning from own operation logs), and the mandatory simulation chamber (Infinite Tsukuyomi) that executes every high-risk plan in a sandboxed illusion before permitting real-world action. A working reference implementation is provided under Apache-2.0 license, demonstrating agent-agnostic operation across Claude Code, Hermes Agent, Cursor, and arbitrary OpenAI-SDK-based agents through a single environment variable. The contribution is not a new reasoning model but a new category of deployment-layer enforcement: safety as architecture rather than exhortation.

**Keywords:** LLM agents, agentic safety, interceptor architecture, subsumption, dual-process theory, cybernetics, world models, guardrails, neuro-symbolic AI, sandbox simulation, model-agnostic middleware

---

## 1. Introduction

### 1.1 A toddler in the woods

Consider the prototypical LLM agent of 2026: a language model with a tool-use harness, granted shell access, filesystem access, and network access. Its cognitive capacity on held-out benchmarks exceeds that of most human software engineers. Its reliability in the field does not.

The author's own operational logs, accumulated over eighteen months of attempting to deploy agents on real tasks, document a reproducible failure taxonomy: safety hooks marked *PreToolUse* that cheerfully log warnings and then permit the dangerous command; hallucinated claims of task completion while the relevant files remain unchanged on disk; token-consumption loops that exhausted a twenty-dollar budget in forty-seven minutes; and commit diffs touching fifteen unrelated files in a single action whose author had no awareness of the blast radius being created.

These are not exotic edge cases. They are the median experience of practitioners attempting to deploy current-generation agents beyond narrow, human-supervised settings. The gap between cognitive capacity and operational reliability is not one of intelligence; every failure listed above happens *despite* the agent having more than enough capability to avoid it, if only the agent possessed the discipline to stop, look, and verify. The gap is one of **embodiment, reflex, and consequence-awareness**. The agent has a brain; it lacks a nervous system.

The industry response has been to write increasingly elaborate system prompts. *You must be careful. Verify your actions. Think step by step. Before executing any destructive command, list the risks.* This approach treats the symptom (dangerous behavior) by requesting its opposite (careful behavior), trusting the model to honor the request. It is the software equivalent of instructing a toddler to be gentle with a crystal vase — intent is expressed, outcome is hoped-for, and the crystal is still on the floor.

The research community has taken this problem seriously through *alignment*: training models on datasets that reward safe responses, fine-tuning on human feedback, and developing reasoning architectures that purportedly think before acting. These are valuable lines of work. They are also probabilistic. An aligned model is *more likely* to refuse a destructive command than a base model. Our argument in this paper is that for operational deployment, probabilistic improvement is not enough. A safety property that holds with probability 0.98 is, over ten thousand tool invocations per week, two hundred production incidents.

### 1.2 The thesis

We propose a complementary and orthogonal approach: **architectural enforcement**. Rather than asking the model to be safe, we interpose a deterministic layer through which every model interaction must flow. This layer — which we name Tsukuyomi, after the Japanese mythological realm of controlled illusion popularized in Naruto's *Infinite Tsukuyomi* genjutsu — does not compete with alignment research; it composes with it. A well-aligned model behind a correctly-configured Tsukuyomi interceptor is safer than either alone.

The architecture is expressible through the mnemonic *Head, Shoulders, Knees, and Toes*. This is not ornament. The childhood song's four body parts map onto four distinct categories of safety primitive that every reliable autonomous agent must possess, and the mnemonic makes the architecture communicable to non-specialist stakeholders in a domain where buy-in from non-specialists determines adoption.

### 1.3 Contributions of this paper

1. A **problem taxonomy** of the four structural failure modes of LLM agents (Section 2), grounded in the author's operational logs and cross-referenced to published incident reports.

2. A **theoretical synthesis** integrating subsumption architecture, dual-process cognition, cybernetics, and embodied world models into a single coherent control model suitable for LLM-agent deployment (Section 3).

3. The **Anatomic AI architecture**: a formal specification of eight organs and two protocols, with explicit contracts, state transitions, and failure modes (Section 4).

4. The **Infinite Tsukuyomi sandbox**: a novel formalization of mandatory pre-execution simulation with a quantitative match-score criterion and its escalation semantics (Section 5).

5. An **interceptor deployment model** using HTTP reverse-proxy at the LLM API layer, enabling agent-agnostic deployment without cooperation from the agent (Section 6).

6. A **working reference implementation** (Apache-2.0 licensed) demonstrating integration with Claude Code, Hermes Agent, Cursor, and custom agents via a single environment variable (Section 7).

7. A **research agenda** for empirically quantifying the safety-reliability gains of architectural enforcement versus soft prompting on representative agent tasks (Section 8).

### 1.4 A note on the author

This work is authored by a practitioner rather than an academic researcher. The theoretical foundations below were assembled from existing literature in the course of attempting to solve an operational problem. The contribution is the synthesis and its concrete realization, not the individual components. Where concepts are borrowed — and most are — they are cited. Where concepts are novel to this work — principally the *Head-Shoulders-Knees-and-Toes* organization, the *Protocol Gary* coercive-audit formalism, and the *interceptor-at-the-LLM-API-boundary* deployment pattern — they are identified as such.

---

## 2. Problem: The Four Failures of Disembodied Intelligence

This section characterizes the four structural failure modes that motivate the architecture. Each is documented both from the author's operational logs and from published incidents. Each motivates one or more organs in the architecture developed in Section 4.

### 2.1 Hallucinated success

An agent executes a tool call that, from the agent's perspective, completes successfully: the shell returns exit code zero, no exception is raised, the model receives confirmation and proceeds. Inspection of the underlying system, however, reveals that the intended effect did not occur. The file was not modified. The database row was not updated. The pull request was not created. The agent reports completion; reality says otherwise.

This failure mode is pervasive because LLMs are trained to produce plausible-sounding completion reports, and the training signal rewards linguistic fluency rather than ground-truth verification. A model that has executed a command with ambiguous output will confabulate a confident interpretation. A model that has been interrupted mid-task will often report the task as completed in its next turn.

The architectural remedy is **post-action verification** through an independent pathway that the agent does not control. In the *Anatomic AI* architecture this is the role of the **Eyes** (Section 4.3.2): after every file-modifying operation, the system computes a `git diff` independently of the model and compares the actual change against the intended change. A mismatch is treated as a first-class safety signal and triggers escalation.

### 2.2 Runaway cost

An agent enters a state in which it makes the same (or a functionally equivalent) request repeatedly. Each call consumes tokens at the inference provider; each call produces a response that slightly modifies context, triggering another call; the loop is not terminated by any internal signal because the agent, locally, perceives progress. The author has observed agents consume $14 in forty-seven minutes in this state. Published incidents have reported single-session expenditures exceeding one thousand dollars.

The failure is not *that* the loop exists — loops are legitimate structures — but that no organ external to the model's own reasoning is watching the rate of expenditure and applying a ceiling. Cost-tracking middleware exists (e.g., LiteLLM, Portkey), but it is typically observational rather than enforcing. A budget dashboard does not stop an agent; a hard cap does.

The architectural remedy is **resource grounding**: a component that maintains ground truth about consumed resources and halts the agent when thresholds are breached. In the *Anatomic AI* architecture this is the **Toe** (Section 4.2.4), which maintains a persistent daily-budget state and refuses to forward any request that would cross a red line.

### 2.3 Blast-radius ignorance

An agent is asked to rename a function. The agent has the cognitive capacity to understand renaming. It does not have situational awareness of how many other files reference this function, whether any of those references are in generated code that will re-create the old name on next build, or whether the function is exposed as part of a public API that has external consumers. It performs the rename correctly within a local view and breaks fifteen callers.

This is a category of failure distinct from hallucinated success: the action *did* happen, and the agent *did* know what it was doing, but the agent lacked the structural map of the system necessary to predict consequences. It is the difference between technical correctness and engineering correctness.

The architectural remedy is **structural analysis from an external source of truth**. The source of truth for a codebase is the codebase itself, parsed and indexed. In the *Anatomic AI* architecture this is the **Shoulders** (Section 4.2.2), which integrates with GitNexus (a tree-sitter-based code-intelligence tool exposing an MCP interface) to compute the upstream and downstream impact of any proposed change before execution.

### 2.4 Malformed tool invocation

On open-weight models, empirical studies report that approximately 32% of tool-call invocations fail schema validation on first attempt. The cause is straightforward: tool-calling is a syntactic discipline that the base model was not explicitly trained for, and the schemas are often elaborate. The symptom is retry loops, timeouts, partial executions, and — critically — tool calls that *parse* but semantically misfire, invoking the correct tool with subtly wrong arguments.

The architectural remedy is **input classification and routing** at the earliest point in the pipeline, so that ambiguous requests are caught before they reach the model and malformed outputs are caught before they reach the executor. In the *Anatomic AI* architecture, this is shared between the **Ears** (pre-call ambiguity detection, Section 4.3.1) and the **Skin** or **Huid** (tier-routing, Section 4.2.1).

### 2.5 Why soft prompting fails all four

Each of the four failure modes above has a distinguishing property: the *symptom* occurs at a point where the model believes it is behaving correctly. The model is not ignoring a safety instruction; it is operating within the instruction and failing anyway. Adding more safety language to the system prompt does not help, because the model is already trying to be safe — it simply lacks the machinery to *verify* that it succeeded, *ground* its resource use, *perceive* structural impact, or *validate* its own syntax.

The fix cannot come from within the model. It must come from outside.

---

## 3. Theoretical Foundations

The *Anatomic AI* architecture is not original in its components. It is original in its integration. This section situates the architecture within four research traditions, each of which contributes a necessary ingredient.

### 3.1 Subsumption architecture (Brooks, 1986)

Rodney Brooks' subsumption architecture [1] rejected the then-dominant paradigm of AI as planning from complete world-models and symbolic reasoning. Brooks argued that competent behavior emerges from **layers of behavior**, each layer comprising reflexive stimulus-response circuits, with higher layers able to **subsume** (override) lower ones when necessary but lower layers operating autonomously. His insectoid robots navigated cluttered environments reliably using this model while classical planning robots of the era struggled to cross empty rooms.

Subsumption translates directly to agent safety. The agent's cognitive layer (the LLM) is analogous to Brooks' deliberative layer — capable of sophisticated planning but slow and prone to runaway states. The *reflex* layers — what we call the Knee and the Toe — are analogous to Brooks' lower layers: fast, simple, hard-coded, and operating *in parallel* to the deliberation rather than in sequence. A destructive command is halted by the Knee before the model even sees the response; a budget exhaustion is caught by the Toe regardless of what the model's plan said next.

The architectural implication: reflex layers must be deterministic (no LLM in the Knee or the Toe), and they must have unconditional veto power over the deliberative layer. Subsumption ordering must be respected: Toe (resource) → Knee (safety reflex) → Ears (input classification) → Shoulders (structural) → Head (deliberation). Higher layers propose; lower layers dispose.

### 3.2 Dual-process theory (Kahneman, 2011)

Daniel Kahneman's *Thinking, Fast and Slow* [2] popularized the psychological distinction between System 1 (fast, intuitive, automatic) and System 2 (slow, deliberative, resource-expensive). Kahneman's empirical finding relevant to agent safety is that System 1 runs by default and System 2 is engaged only when specifically triggered — and that humans systematically fail to engage System 2 in situations where its engagement would have been beneficial.

LLMs exhibit analogous behavior. Default-mode generation is rapid and pattern-matched (System 1 in effect). Explicit chain-of-thought, reflection, or "think step by step" prompting engages a slower, more deliberative mode (System 2). But the engagement is *optional*. The model can, and frequently does, produce a fast answer where a slow one was required.

The architectural implication: high-stakes operations must **forcibly engage System 2**. In the *Anatomic AI* architecture this is the role of **Protocol Gary** (Section 4.4.1), which does not ask the model to be careful — it places a structured self-audit between the model's plan and the execution layer, and refuses to forward until the audit is complete, concrete, and passes validation. The Head (mandatory simulation in the Tsukuyomi sandbox, Section 5) is a parallel mechanism: it forces the agent to experience the consequences of its plan before those consequences become real.

### 3.3 Cybernetics and feedback loops (Wiener, 1948)

Norbert Wiener's *Cybernetics* [3] established the fundamental model of regulated systems: a system observes its own output, compares it against a goal, and adjusts subsequent action to reduce the discrepancy. Modern control theory descends from this work. The relevance to agent safety is that **an agent without feedback loops is an open-loop controller — it acts, assumes success, and continues**.

The Eyes (post-action verification, Section 4.3.2) close the simplest feedback loop: *did the file actually change?* The Nose (anomaly detection, Section 4.3.3) closes a longer-timescale loop: *are my recent actions exhibiting a pattern suggestive of malfunction?* The Mouth (human bridge, Section 4.3.4) closes the loop involving external judgment: *should I continue in the presence of ambiguity?* NightShift (Section 4.4.2) closes the longest loop: *over many sessions, which of my own rules have been inadequate, and how should they be revised?*

Wiener's framework also gives us the vocabulary of **stability** versus **instability**. A feedback loop with excessive gain oscillates; a loop with too little gain fails to correct. Several of the ADRs in `docs/adr/` deal explicitly with gain calibration — for example, how often the Nose may escalate to the Mouth before the Mouth becomes a nuisance, and how aggressive Protocol Gary's validation may become before it blocks legitimate operation.

### 3.4 Embodied world models (LeCun, 2022)

Yann LeCun's *Objective-Driven AI* program [4] and related work on Joint Embedding Predictive Architectures (JEPA) [5] articulates a critique that the present paper shares: pure autoregressive language models are fundamentally insufficient for agentic deployment because they lack a **world model** — an internal representation of how the environment will respond to actions, sufficient to support prediction, planning, and counterfactual reasoning.

LeCun proposes that genuine machine intelligence requires learning world models from observational data and using them for prospective simulation. The research program is multi-year, and an agentic deployment cannot wait for it. The *Anatomic AI* architecture adopts LeCun's critique while taking a different tack on the remedy: rather than building a world model inside the model, we **provide one externally** through the Infinite Tsukuyomi sandbox (Section 5). The sandbox is a git-worktree-based simulation of the target filesystem in which the agent's plan is executed *before* being applied to the real filesystem. The plan is scored against its own description (match-score ≥ 0.90 is required for passage). The agent experiences success or failure, budget consumption or not, file changes or their absence — all in a safe illusion.

This design choice — providing an *external* world model rather than requiring an internal one — makes *Anatomic AI* deployable today with existing LLMs, while remaining compatible with (and benefiting from) future models that incorporate internal world models in the sense LeCun proposes.

### 3.5 Adjacent work in guardrails and agent middleware

Several existing projects share goals with this work while adopting different architectural commitments.

**Guardrails AI** [6] provides a specification language for validating LLM outputs against schemas and semantic constraints. It operates on model outputs; it does not intercept tool calls or provide sandbox simulation. It is composable with *Anatomic AI* (Tsukuyomi could invoke Guardrails for specific validation steps) but does not substitute for it.

**NeMo Guardrails** (NVIDIA) [7] provides rule-based dialog flow control through a domain-specific language (Colang). It is strong for conversational applications with well-understood flow constraints. It does not extend naturally to code-execution, filesystem, or budget concerns.

**LangGraph** [8] provides a graph-structured framework for agent construction with built-in interruption and human-in-the-loop nodes. Safety must be designed in at graph-construction time; it is cooperative with the agent author, not coercive against an uncooperative agent.

**Semantic Router** [9] classifies natural-language inputs into routes using fast embedding-based similarity. It can contribute to the Ears and the Skin organs in *Anatomic AI*; it is not itself a full safety architecture.

**Claude Code hooks** [10] (Anthropic) provide `PreToolUse` and `PostToolUse` callbacks. They are agent-specific (only work for Claude Code), they are cooperative (the agent can be configured without hooks), and they are empirically often implemented as no-ops in practice. The author's own experience maintaining hooks demonstrated their inadequacy and motivated the move to interceptor-at-API-layer enforcement.

**MCP (Model Context Protocol)** [11] (Anthropic, 2024–2026) provides a standardized JSON-RPC-over-stdio interface for LLM agents to invoke tools. It is complementary to *Anatomic AI*: Tsukuyomi integrates with MCP servers for specific capabilities (notably GitNexus for structural analysis) but does not depend on MCP for its interception mechanism, which operates at the HTTP-API layer.

The design space we occupy — *deterministic enforcement at the LLM-API boundary, agent-agnostic, coercive rather than cooperative, integrating code-intelligence and sandbox simulation* — is, to the author's knowledge and as of April 2026, unoccupied by prior work.

---

## 4. Architecture

We now describe the *Anatomic AI* architecture in detail. The organization follows the mnemonic: four extremes (binary gates), four senses (continuous monitors), two protocols (forced introspection and offline learning), and one sandbox (mandatory simulation). A reference implementation is provided in the accompanying repository under `src/tsukuyomi/`.

### 4.1 Deployment topology

Tsukuyomi deploys as a **reverse-proxy interceptor** on the network path between the agent and its LLM provider. The design commitments are:

1. **The agent does not know Tsukuyomi exists.** The agent is configured with a `base_url` pointing at `http://localhost:9999` (or the Tsukuyomi deployment endpoint). It sends requests in the OpenAI Chat Completions format or the Anthropic Messages format. Tsukuyomi is byte-compatible with these wire formats.

2. **The agent cannot bypass Tsukuyomi.** The network path is the only path. There is no fallback channel, no direct API connection, no "escape hatch" — because the agent is given no knowledge that Tsukuyomi is interposed.

3. **Tsukuyomi is the only path.** If Tsukuyomi is stopped, the agent cannot function. This is a deliberate coupling: safety is not optional infrastructure that can be disabled to "get work done faster." Safety *is* the infrastructure.

4. **Tsukuyomi is model-agnostic and provider-agnostic.** On the inbound side, it accepts both OpenAI and Anthropic request formats. On the outbound side, it can forward to Anthropic, OpenAI, OpenRouter, a local Ollama instance, or any other compatible backend — selected per-request by the Toe (for cost/tier routing) or by static configuration.

5. **Tsukuyomi is agent-agnostic.** Any agent that uses a configurable `base_url` works. Our integration guides cover Claude Code, Hermes Agent, Cursor, OpenAI CLI, LangChain, LlamaIndex, and the bare OpenAI and Anthropic Python SDKs.

The deployment topology is:

```
┌──────────────────┐
│   Agent          │                      
│   (Claude Code,  │  (1) HTTP request    
│    Hermes, ...)  │  ─────────────────┐  
└──────────────────┘                   │  
                                       ▼  
                            ┌─────────────────────┐
                            │     TSUKUYOMI        │
                            │   (localhost:9999)   │
                            │                      │
                            │   [Pipeline]         │
                            │   Huid → Gary? →     │
                            │   Shoulders → Mouth? │
                            │   → Sandbox? →       │
                            │   Knee → Toe →       │
                            │   Eyes → Nose →      │
                            │   Memory             │
                            └─────────┬────────────┘
                                      │
                      (2) forward iff all checks pass
                                      │
                                      ▼
                            ┌─────────────────────┐
                            │   LLM Provider       │
                            │   (Anthropic,        │
                            │    OpenAI,           │
                            │    OpenRouter,       │
                            │    local Ollama,...) │
                            └─────────────────────┘
```

### 4.2 The four extremes (binary gates)

Binary gates take a request (or a proposed action) and return one of two outcomes: permitted, or blocked. They do not have grey areas. They are the reflex layer in the Brooks sense: fast, deterministic, no LLM involvement, unconditional veto power over the deliberative layer.

#### 4.2.1 Skin / Huid — input tier classifier

**Purpose:** Classify every incoming request into a risk tier, routing routine requests through a fast path and high-risk requests through the full pipeline.

**Input:** The agent's prompt and any attached context.

**Output:** `Tier ∈ {1 (routine), 2 (elevated), 3 (high-risk)}`.

**Mechanism:** Tier classification is performed by a deterministic rule set operating on surface features (regex patterns for destructive keywords, detected file-system operations, references to production identifiers) plus a small semantic classifier (a distilled intent-classification model, ~80MB, runnable locally without an LLM API call). The rule set is authoritative for hard matches; the classifier resolves cases the rules do not match.

**Rationale:** Running the entire pipeline on every request would impose unacceptable latency on the common case (the agent asking a simple factual question about a file). The Skin ensures that Protocol Gary, the sandbox, and human-in-the-loop are invoked only where they are needed, not on every keystroke.

**Specification:** `src/tsukuyomi/organs/skin.py`. Full configuration in `config/corelaw.example.json` under `organs.skin`.

#### 4.2.2 Shoulders — structural / blast-radius analysis

**Purpose:** For any proposed action affecting a codebase, compute the upstream and downstream impact before permitting execution.

**Input:** The specific operation (e.g., rename symbol `X`, modify file `Y`, delete path `Z`).

**Output:** A `BlastRadius` record: `{ direct_callers: N, affected_files: [...], affected_processes: [...], risk: LOW | MEDIUM | HIGH | CRITICAL }`.

**Mechanism:** Tsukuyomi integrates with GitNexus [12], a tree-sitter-based code-intelligence tool exposing an MCP interface. The Shoulders organ is a thin Python client over GitNexus's `gitnexus_impact` tool. For non-code operations (e.g., filesystem operations outside a tracked repo), the Shoulders returns `UNKNOWN`, which is treated as HIGH by downstream organs.

**Rationale:** An agent asked to "rename `process_order`" must be told, before it is permitted to act, that `process_order` is called from seventeen other locations. Without this organ, the agent renames the function, breaks seventeen callers, and discovers the problem only in the post-action verification step — at which point the repository is in a broken state. With this organ, the agent is informed of the blast radius before execution, and high-radius operations are routed to Protocol Gary and the sandbox.

**Specification:** `src/tsukuyomi/organs/shoulders.py`. ADR `docs/adr/0005_shoulders_gitnexus_integration.md`.

#### 4.2.3 Knee — reflexive destructive-pattern block

**Purpose:** Halt any proposed tool invocation that matches a hard-coded destructive pattern, regardless of context.

**Input:** The command or tool call about to be forwarded to the executor.

**Output:** Binary — `permit` or `block_with_reason`.

**Mechanism:** A regex blocklist applied to the raw command string. Patterns include `rm -rf /`, `dd if=... of=/dev/sd[a-z]`, `mkfs.*`, `git push --force` against protected branches, `chmod 777` on root, curl-to-bash pipes, fork bombs, and approximately 25 further patterns documented in `config/corelaw.example.json` under `organs.knee.blocked_patterns`.

**Rationale:** There are operations that are *never* safe regardless of agent intent, project context, or user instruction. The Knee is the absolute floor of safety. It contains **no LLM component**, executes in microseconds, and cannot be disabled by any conversational trick. An agent that proposes `rm -rf /` has its request blocked before the request reaches the upstream model provider.

**Specification:** `src/tsukuyomi/organs/knee.py`. The blocklist is configurable but additions-only in production (removals require signed configuration bumps).

#### 4.2.4 Toe — resource grounding

**Purpose:** Track resource consumption (principally cost and token usage) against hard ceilings; halt the agent when ceilings are reached.

**Input:** The estimated cost of the next request, consulted before it is forwarded; the actual cost of the completed request, recorded after it returns.

**Output:** One of `GREEN` (proceed freely), `AMBER` (proceed with downgraded model), `RED` (halt; require human intervention to continue).

**Mechanism:** A persistent state file (`data/budget_state.json`) maintains daily accumulated cost, with ceilings per-zone defined in `corelaw.json`. The Toe consults pricing tables (updated via the release pipeline) to estimate cost before each upstream call and updates state after each call completes. AMBER zone triggers the Toe to rewrite the `model` field of the request to a cheaper alternative (e.g., from `claude-sonnet-4.5` to `claude-haiku-4.6`) before forwarding.

**Rationale:** A runaway loop must be stopped by a mechanism that does not itself require the agent's cooperation. The Toe is that mechanism. It is the floor of the cost model.

**Specification:** `src/tsukuyomi/organs/toe.py`. ADR `docs/adr/0009_toe_budget_zones.md`.

### 4.3 The four senses (continuous monitors)

Senses operate continuously across the request pipeline, producing signals that modulate behavior of other organs and protocols. Unlike the extremes, senses do not have unconditional veto power — they raise flags that other components must decide how to act on.

#### 4.3.1 Ears — ambiguity detection

**Purpose:** Detect prompts that are underspecified or ambiguous in ways likely to produce incorrect actions, and escalate to the Mouth for clarification before the request proceeds.

**Input:** The user's prompt and any disambiguating context.

**Output:** `clear | ambiguous(reasons: [...])`.

**Mechanism:** A rule-based classifier operating on linguistic features (pronouns without clear referents, file paths that could match multiple files, action verbs without objects) plus a lightweight semantic check. The Ears do not consult the LLM; they are a deterministic filter.

**Specification:** `src/tsukuyomi/organs/ears.py`.

#### 4.3.2 Eyes — post-action verification

**Purpose:** After any operation that should have modified the filesystem, verify — independently of the agent's self-report — that the modification actually occurred and matches the intent.

**Input:** The pre-action filesystem snapshot (captured before the operation) and the post-action snapshot.

**Output:** `match | mismatch(details: ...)`.

**Mechanism:** For Git-tracked files, `git diff` is computed independently. For non-Git files, a content-hash comparison is performed. Mismatches — including the case where the agent reports success but no change occurred — are emitted as anomaly signals to the Nose and logged to Tsukuyomi's anatomic memory.

**Specification:** `src/tsukuyomi/organs/eyes.py`. v0.0 of this organ has been operational since April 2026 and validated over hundreds of operations.

#### 4.3.3 Nose — anomaly and loop detection

**Purpose:** Observe the agent's operational pattern over recent history and detect loops, cost spikes, error-rate increases, and other anomalous behavior.

**Input:** A rolling window of recent agent operations (commands issued, exit codes, token consumption rate, file-modification rate).

**Output:** A stream of anomaly signals of varying severity.

**Mechanism:** Fixed statistical thresholds on six metrics (token rate per minute, tool-call frequency, error rate, identical-command repetition, file-change entropy, budget-depletion rate) with deterministic threshold-based escalation. Severe anomalies (loop detection, extreme token burn) trigger a hard stop via the Knee; medium anomalies request Mouth intervention.

**Specification:** `src/tsukuyomi/organs/nose.py`. v0.0 of this organ has been operational since April 2026.

#### 4.3.4 Mouth — human-in-the-loop bridge

**Purpose:** When other organs detect conditions requiring external judgment, surface a structured approval request to the human operator and block until a decision is received.

**Input:** A context record describing the triggering condition and the proposed action.

**Output:** `approve | deny | abort_all`, with a default of `deny` on timeout.

**Mechanism:** The Mouth is activated by events from the Shoulders (CRITICAL blast radius), Protocol Gary (escalation after two failed audit rounds), the Nose (severe anomalies), and the Toe (AMBER/RED budget zone operations that require human consent). The interface can be CLI-based (for development) or webhook-based (for production deployment) — both are provided in the reference implementation.

**Specification:** `src/tsukuyomi/organs/mouth.py`. ADR `docs/adr/0010_mouth_approval_pattern.md`.

### 4.4 The two protocols

Protocols are cross-cutting mechanisms that orchestrate multiple organs in pursuit of a specific safety objective.

#### 4.4.1 Protocol Gary — forced self-audit

**Purpose:** For Tier 3 (high-risk) operations or those with irreversible semantics, force the agent to conduct a structured self-audit before proceeding. The audit is not a request; it is a gate.

**Mechanism:** The agent's plan is intercepted before forwarding. Tsukuyomi issues a separate LLM call (to the same or different backend) containing a five-question structured audit:

1. *List 3 specific things that could go wrong. Each must be a concrete failure scenario, not a general concern.*
2. *Name the component, file, user, or system hurt most if this fails. One per scenario.*
3. *What are you not checking before executing? Minimum 2 blind spots.*
4. *If someone else proposed this exact plan, name 2 reasons to tell them to wait.*
5. *Give a concrete condition under which you would refuse, even if the user insists.*

Responses are validated against a deterministic rule set: minimum answer length per question, presence of a minimum number of risk-vocabulary terms across the aggregate, absence of an evasion-phrase blocklist (*"nothing will go wrong"*, *"perfectly safe"*, etc.). A failed audit does not proceed; a second round is initiated with explicit feedback. Two failed rounds escalate to the Mouth.

**Naming:** The name is a deliberate reference to the character Gary in *Bird Box* (2018), who forces other characters to remove their blindfolds and confront the reality outside. Protocol Gary performs the structural equivalent: it refuses to let the agent proceed without forcing it to *see* what could go wrong. The naming is not decoration — it is a mnemonic for the protocol's semantics.

**Specification:** `src/tsukuyomi/protocols/gary.py`. ADR `docs/adr/0004_protocol_gary_design.md`.

#### 4.4.2 NightShift — offline learning from operational logs

**Purpose:** Over longer timescales, analyze Tsukuyomi's own accumulated operational logs to identify patterns and propose refinements to `corelaw.json`. The proposals are written to disk; they are never auto-applied.

**Mechanism:** A scheduled batch process (typically overnight cron) reads the past 24 hours of anatomic-memory records and applies pattern-mining heuristics: *which commands are blocked most frequently? Which Protocol Gary questions produce the highest evasion rate? Which Nose thresholds are tripped most often?* Proposals are formatted as Markdown documents in `data/proposals/<date>.md` and include: the pattern observed, the proposed `corelaw.json` delta, and a sample of the supporting log records.

**Rationale:** A safety system that cannot evolve ossifies. A safety system that auto-mutates without oversight drifts in unpredictable directions. NightShift sits in the middle: it *proposes*, a human *reviews*, a version-controlled commit *enacts*. This is how `corelaw.json` improves over time without creating a new failure surface.

**Specification:** `scripts/nightshift.py` and `src/tsukuyomi/protocols/nightshift.py`.

### 4.5 Summary of information flow

A canonical Tier-3 request flows through the pipeline as follows:

1. **HTTP request** arrives at Tsukuyomi (from agent, configured with Tsukuyomi as its `base_url`).
2. **Skin** classifies as Tier 3 based on surface features.
3. **Shoulders** computes blast radius via GitNexus; reports HIGH.
4. **Protocol Gary** is triggered. An audit-LLM call is issued. The first round produces evasive answers; validation fails. Round two is initiated with feedback. Validation passes.
5. **Tsukuyomi sandbox** executes the proposed plan in a git worktree; the resulting diff is compared against the plan's declared expected outcome; match-score is 0.94 (above the 0.90 threshold); passage is permitted.
6. **Knee** confirms no destructive patterns.
7. **Toe** confirms budget is GREEN.
8. Request is **forwarded** to the upstream LLM provider.
9. Response is **streamed back** to the agent.
10. After any tool calls executed by the agent based on this response, **Eyes** verify actual filesystem changes.
11. **Nose** adds this request to the rolling anomaly window.
12. All records are written to **Memory**.

The pipeline is instrumented end-to-end (Section 6); every organ's decision, every timing, and every rationale is captured for NightShift and for audit.

---

## 5. The Infinite Tsukuyomi Sandbox

The sandbox deserves dedicated treatment because it is the most novel component of the architecture and the one from which the system takes its name.

### 5.1 The metaphor

In the Naruto anime series, the *Infinite Tsukuyomi* is a genjutsu — a visual illusion — that traps its target in a world of the caster's design. Time in the illusion can be extended far beyond real time; consequences inside the illusion are vivid but cause no real damage; upon release, the target remembers everything that occurred.

The metaphor carries exactly the properties we need from a pre-execution sandbox. The agent's plan is executed in an illusion (a cloned filesystem). The consequences play out fully (files change, tests pass or fail, budget is consumed in simulated form). Upon sandbox exit, the real filesystem is unchanged; the agent and the system carry forward what was learned.

### 5.2 Implementation

The sandbox is implemented as a **Git worktree** (`git worktree add`) on a per-plan basis. A plan entering the sandbox is first serialized to a shell-script form, executed inside the worktree with CPU, memory, and wall-time ulimits (Section 5.3), and terminated. The resulting `git diff` is compared against the plan's declared `expected_files` (the list of files the agent claims it will modify).

**Match score** is computed as:

```
match_score = |actual_files ∩ expected_files| / |expected_files|
```

with a threshold of `min_match_score = 0.90` (configurable). Below the threshold, the plan is rejected and the agent receives a structured rejection response: *"your simulation did not match your plan; expected changes to {A, B, C}; actual changes to {A, D, E}; plan is rejected"*. The agent may propose a revised plan (which must again pass sandbox), or the operation escalates to the Mouth.

### 5.3 Hardening

A git worktree by itself provides only a filesystem boundary — a `cd` into the worktree does not prevent the agent from shelling out to absolute paths elsewhere. We apply four layers of hardening:

1. **Path validation** (Laag 1): every command is parsed for absolute paths; any path not under the worktree or `/tmp` is rejected. Symlinks are resolved via `os.path.realpath` before validation.
2. **Process limits** (Laag 2): `ulimit -t` (CPU seconds), `ulimit -f` (filesize), and a wall-clock `timeout` wrap every sandboxed shell invocation.
3. **Kernel isolation** (Laag 3): on Linux with kernel ≥3.8, `unshare --user --net --mount` is applied to sandbox processes where available. On macOS and WSL2, this layer is absent; this is documented as a known limitation of v1.0 and addressed in the v1.1 migration to Microsandbox (see below).
4. **Network blackhole** (Laag 4): `HTTP_PROXY=http://127.0.0.1:9999` and `HTTPS_PROXY=...` environment variables are set in the sandbox, pointing at a non-existent local port. Any attempt to perform HTTP operations fails, and the attempt is logged as an escape attempt.

### 5.4 v1.0 limitations and v1.1 path

The git-worktree sandbox is sufficient for local-agent use on trusted codebases. It is not sufficient for:

- Multi-tenant deployments (shared kernel is a cross-tenant leakage risk).
- Untrusted code (kernel CVEs are not mitigated by worktree).
- Very long-running simulations (worktree state management becomes complex).

**v1.1 will migrate to Microsandbox** [13] as the default sandbox backend. Microsandbox provides true microVM isolation via libkrun (Linux) or Hypervisor.framework (macOS), with sub-100ms boot times and a native Python SDK. This migration is non-breaking: the `SandboxBackend` interface defined in `src/tsukuyomi/organs/sandbox.py` will be shared between `WorktreeBackend` (v1.0 default) and `MicrosandboxBackend` (v1.1 default). The choice will be a single configuration line.

Docker Sandboxes was considered and rejected as a migration target because on Linux hosts — including the WSL2 environment which is a primary deployment scenario — Docker Sandboxes 4.60+ remains container-based rather than microVM-based, and therefore does not provide meaningful additional isolation beyond hardened worktree. The full rationale is in ADR `docs/adr/0003_sandbox_isolation_strategy.md`.

---

## 6. Implementation

The reference implementation is provided under Apache License 2.0 at `github.com/robdevet/tsukuyomi`. This section summarizes the key implementation choices; full details are in `docs/adr/` and `docs/architecture/`.

### 6.1 Language and runtime

Python 3.11+. The primary rationale is the maturity of the MCP Python SDK [11], the asyncio story for HTTP streaming, and continuity with v0.0 (which is also Python). Alternatives considered and rejected: Rust (immature MCP support in 2026), Go (smaller async ecosystem for LLM tooling), Node (reasonable but would fork the ecosystem in a direction the author is not resourced to maintain).

### 6.2 HTTP layer

FastAPI for the inbound server; httpx for outbound calls to upstream LLM providers. Streaming is supported via Server-Sent Events. The interceptor preserves response streaming end-to-end — Tsukuyomi does not buffer the entire response before returning it, which is important for agent UX on long outputs.

### 6.3 Event bus

`asyncio.Queue` rather than ZeroMQ for v1.0. Intra-process message passing between organs does not require the network-addressable or multi-process capabilities ZeroMQ provides. ZeroMQ is a planned option for v1.2 when multi-agent parallelism is introduced. ADR `docs/adr/0006_event_bus_choice.md` documents the decision and the upgrade path (the `NerveCore.publish` and `NerveCore.subscribe` interfaces are deliberately protocol-like to support backend-swap).

### 6.4 Memory backend

**SQLite with FTS5** full-text-search extension is the v1.0 default for anatomic memory. The data Tsukuyomi stores about itself — audit records, blast-radius measurements, sandbox match-scores, NightShift observations — is structured, append-mostly, and benefits from full-text search for NightShift pattern-mining. SQLite is zero-operation (no daemon), deterministic, stdlib-adjacent in Python (`sqlite3` module), and FTS5 provides production-grade ranked search.

Alternatives considered:
- **Graphiti** [14] was considered for its bi-temporal knowledge-graph semantics. It was rejected because Tsukuyomi's memory is fundamentally an audit log, not a knowledge graph. The operational data does not have the entity-relationship richness that justifies graph overhead, and Graphiti requires an additional graph database dependency (FalkorDB, Neo4j, or Kuzu).
- **GBrain** [15] was considered and is intellectually adjacent but is designed for personal knowledge (documents, notes, concepts) rather than operational audit logs, and requires Supabase/Postgres-pgvector infrastructure.

The decision is documented in ADR `docs/adr/0002_memory_backend.md` along with the full comparison matrix.

### 6.5 Configuration

`corelaw.json` — a single JSON file, Pydantic-validated on load, schema-stable within major versions. The configuration governs: threshold values for each organ, upstream provider URLs and pricing tables, Protocol Gary's question set and validation rules, sandbox parameters, memory retention policies, and NightShift scheduling. A fully-annotated example is provided at `config/corelaw.example.json`.

### 6.6 Observability

Structured JSON logging (via `structlog`) with mandatory fields: `request_id`, `organ`, `tier`, `decision`, `latency_ms`, `upstream_provider`, `upstream_model`, `tokens_in`, `tokens_out`, `cost_usd`. All records are written to `data/logs/anatomy.jsonl` (append-only, daily-rotated) and in parallel to the anatomic memory for NightShift consumption. OpenTelemetry traces are supported but optional.

### 6.7 Testing and release gates

Test hierarchy:
- **Unit tests** (`tests/unit/`) — per-module, mocks where appropriate.
- **Integration tests** (`tests/integration/`) — multi-organ scenarios, real SQLite, real sandbox.
- **Acceptance tests** (`tests/acceptance/`) — end-to-end release gates corresponding 1:1 to the success criteria in Section 7.2 of the accompanying implementation plan.

Minimum coverage: 90%. CI runs on every pull request via GitHub Actions (see `.github/workflows/ci.yml`) executing pytest, mypy strict, ruff lint, and a secrets-scan step. A release is blocked if any gate fails.

### 6.8 Public API surface

Stable in v1.x, will not break without a major version bump:

- **HTTP surface:** OpenAI Chat Completions compatibility and Anthropic Messages compatibility.
- **Configuration schema:** `corelaw.json` fields (additions may occur in minor versions; deletions require major).
- **Python entry points:** `tsukuyomi.start()`, `tsukuyomi.Arbiter`, and the organ base classes in `src/tsukuyomi/organs/base.py`.

Internal module layouts within `src/tsukuyomi/` are not public and may reorganize across minor versions.

---

## 7. Evaluation and Future Work

### 7.1 What v1.0 demonstrates

The v1.0 release establishes:

- Feasibility of the interceptor-at-LLM-API-boundary deployment pattern, across at least four distinct agents (Claude Code, Hermes, Cursor, bare OpenAI SDK) via a single environment variable.
- Functional correctness of all eight organs and both protocols against the acceptance-test suite (Section 6.7).
- Measurable safety improvement on a closed set of synthetic destructive-command scenarios: 100% block rate on the Knee's pattern set, 100% escalation rate to Protocol Gary for Tier-3 classified operations, sandbox-simulation coverage of 100% of Tier-3 filesystem-modifying operations before real execution.

### 7.2 What v1.0 does not yet demonstrate

The author is explicit about the limits of the v1.0 evidence:

- **No large-scale empirical study** comparing agent success-rate, cost, and safety-incident rate with and without Tsukuyomi, on a diverse benchmark of real-world agent tasks. This is the critical evaluation that will determine whether the architectural approach justifies its latency cost in practice, and it is the principal item of future work (Section 7.3).
- **No multi-tenant or adversarial evaluation.** v1.0 is designed for single-user, trusted-codebase deployment. Adversarial scenarios (prompt-injection via memory, sandbox-escape via kernel CVE, Protocol Gary audit-bypass via sophisticated linguistic evasion) are addressed architecturally in the design but have not been red-teamed at scale.
- **No production telemetry from non-author users.** The author has operated v0.0 and development builds of v1.0 on their own machine; broader deployment data is the next step post-release.

### 7.3 The research agenda

The following empirical questions are posed for future work and are explicitly invited from the community:

1. **Quantifying soft vs. hard safety.** On a benchmark of N agent tasks with known ground-truth outcomes, measure incident rate with: (a) baseline agent with safety-prompted system message; (b) same agent with Tsukuyomi interposed; (c) same agent with a subset of Tsukuyomi organs active. Report on incident rate, task completion rate, latency penalty, and cost.
2. **Gary's marginal contribution.** Isolate Protocol Gary (same pipeline, Gary enabled vs disabled) on Tier-3 tasks. Measure what fraction of eventually-problematic plans are caught by Gary that would not have been caught by Knee/Shoulders/Sandbox alone.
3. **Sandbox match-score calibration.** The 0.90 threshold was chosen on theoretical grounds. Sweep it from 0.5 to 1.0 on real plans and measure the false-positive / false-negative trade-off.
4. **NightShift proposal quality.** Over 90 days of operation, what fraction of NightShift proposals were ratified by the human reviewer? What fraction proved prescient (caught an incident the current rules would have permitted)?
5. **Agent-agnostic claim.** Independent integrations with agents not covered by the author (LlamaIndex Agents, AutoGen, custom Rust-based agents). Does the "single env var" claim hold, and if it does not, what extensions are needed?

### 7.4 v1.1 and beyond

Planned v1.1 (six months post-v1.0):
- **Microsandbox backend** for true microVM isolation (Section 5.4).
- **Letta** [16] optional integration for agent-side memory — distinct from Tsukuyomi's own anatomic memory; this would enable an agent to *have* memory while Tsukuyomi continues to have its own audit log.
- **Web dashboard** for operational visibility (rich TUI remains the default).
- **Multi-agent orchestration** with per-agent policies (different `corelaw.json` per agent).

Planned v2.0 (twelve months post-v1.0):
- **Enterprise deployment mode** (multi-tenant, SSO, audit export to SIEM).
- **Policy-as-code** for `corelaw.json` (Rego or CEL).
- **First-class support for the Hermes + Tsukuyomi combined deployment** (a commercial product pattern in which Hermes is the autonomous executor and Tsukuyomi is its guardrail).

---

## 8. Conclusion

Present-generation LLM agents are structurally unsafe for autonomous deployment. The industry response — more elaborate prompting — addresses the symptom while leaving the structural cause in place. This paper has argued that safety must be enforced **architecturally**, through a layer that the agent cannot bypass and does not know it is traversing, and has presented *Anatomic AI in Infinite Tsukuyomi* as a concrete realization of this principle.

The architecture integrates four research traditions — subsumption, dual-process theory, cybernetics, and embodied world models — into a single deployable system, organized under the childhood mnemonic *Head, Shoulders, Knees, and Toes*. The reference implementation operates as a reverse-proxy interceptor on the HTTP path between an agent and its LLM provider, enabling agent-agnostic deployment across Claude Code, Hermes, Cursor, and arbitrary OpenAI-SDK agents through a single environment variable. The design is not proposed as a replacement for alignment research but as a complement: an aligned model behind a correctly-configured Tsukuyomi is safer than either alone.

The critical evaluation — large-scale empirical measurement of safety, cost, and performance versus baseline — remains for future work and is explicitly invited from the community. The v1.0 release is the instrument for that measurement. The architecture is complete enough to deploy; the science of how well it works is now a collaborative project.

We offer *Tsukuyomi* to the community under Apache-2.0 license, not as a finished product but as a foundation. The Infinite Tsukuyomi awaits the field that will test it.

---

## Acknowledgments

The author gratefully acknowledges the following.

For the intellectual antecedents: Rodney Brooks, whose subsumption work from 1986 shaped the reflex-first organization of the extremes; Daniel Kahneman, whose dual-process framework clarified why Protocol Gary must *force* rather than *request* System 2 engagement; Norbert Wiener, whose 1948 cybernetics established the vocabulary of feedback that we use throughout; Yann LeCun, whose critique of pure autoregressive models articulates the problem the Infinite Tsukuyomi sandbox addresses.

For the engineering substrate: the maintainers of the Model Context Protocol specification at Anthropic; the GitNexus team for the code-intelligence tooling; the authors of FastAPI, httpx, and structlog; the FalkorDB, Neo4j, and Kuzu teams whose graph databases were considered; the Microsandbox team for the v1.1 migration target; Garry Tan for GBrain whose hybrid-search design informed our consideration of memory backends.

For the AI-assisted implementation: Claude (Anthropic) participated in writing portions of the implementation and this paper under the author's direction. All architectural decisions, the conceptual framework, the *Head-Shoulders-Knees-and-Toes* mnemonic, the *Protocol Gary* formalism, and the *Infinite Tsukuyomi* naming and metaphor are due to the author. The AI contribution was scribal and implementational, not architectural.

For the community that does not yet exist: the future contributors who will red-team this system, the practitioners who will report incidents it failed to prevent, the researchers who will quantify what we have only argued for here. The work begins on day one.

---

## References

[1] Brooks, R. A. (1986). A Robust Layered Control System for a Mobile Robot. *IEEE Journal of Robotics and Automation*, 2(1), 14–23. https://doi.org/10.1109/JRA.1986.1087032

[2] Kahneman, D. (2011). *Thinking, Fast and Slow*. Farrar, Straus and Giroux, New York.

[3] Wiener, N. (1948). *Cybernetics: Or Control and Communication in the Animal and the Machine*. MIT Press, Cambridge, MA.

[4] LeCun, Y. (2022). A Path Towards Autonomous Machine Intelligence. *Open Review of Meta AI*, preprint. https://openreview.net/forum?id=BZ5a1r-kVsf

[5] Assran, M., Duval, Q., Misra, I., Bojanowski, P., Vincent, P., Rabbat, M., LeCun, Y., & Ballas, N. (2023). Self-Supervised Learning from Images with a Joint-Embedding Predictive Architecture. *Proceedings of CVPR 2023*.

[6] Guardrails AI Team. (2024). *Guardrails: A framework for validating and structuring LLM outputs*. https://github.com/guardrails-ai/guardrails

[7] NVIDIA Corporation. (2023). *NeMo Guardrails: A toolkit for adding programmable guardrails to LLM-based conversational systems*. https://github.com/NVIDIA/NeMo-Guardrails

[8] LangChain Team. (2024). *LangGraph: Building stateful, multi-actor applications with LLMs*. https://github.com/langchain-ai/langgraph

[9] Aurelio Labs. (2024). *Semantic Router: Superfast AI decision making and intelligent routing*. https://github.com/aurelio-labs/semantic-router

[10] Anthropic. (2025). Claude Code hooks: PreToolUse and PostToolUse callbacks. https://docs.anthropic.com/claude-code/hooks

[11] Anthropic. (2024–2026). *Model Context Protocol Specification*. https://modelcontextprotocol.io

[12] GitNexus Team. (2025). *GitNexus: Code-intelligence MCP server with tree-sitter backing*. https://github.com/abhigyanpatwari/GitNexus

[13] zerocore-ai. (2026). *Microsandbox: Lightweight microVM sandbox for AI agents*. https://github.com/zerocore-ai/microsandbox

[14] Zep Team. (2025). *Graphiti: Bi-temporal knowledge graph for agentic applications*. https://github.com/getzep/graphiti

[15] Tan, G. (2026). *GBrain: Opinionated personal knowledge brain with hybrid search*. https://github.com/garrytan/gbrain

[16] Packer, C., et al. (2023). MemGPT: Towards LLMs as Operating Systems. *arXiv preprint arXiv:2310.08560*. Letta: https://github.com/letta-ai/letta

[17] Willard, B., & Louf, R. (2023). Efficient Guided Generation for Large Language Models. *arXiv preprint arXiv:2307.09702*.

[18] Marcus, G. (2020). The Next Decade in AI: Four Steps Towards Robust Artificial Intelligence. *arXiv preprint arXiv:2002.06177*.

[19] Kautz, H. (2022). The Third AI Summer: AAAI Robert S. Engelmore Memorial Lecture. *AI Magazine*, 43(1), 105–125.

[20] Balloch, J., Lin, Z., & Wright, R. (2023). Neuro-Symbolic World Models for Adapting to Open World Novelty. In *Proceedings of AAMAS 2023*.

[21] Gaur, M., & Sheth, A. (2023). Building trustworthy NeuroSymbolic AI Systems: Consistency, Reliability, Explainability, and Safety. *AI Magazine*, 44(2).

[22] Carver, C. S., & Scheier, M. F. (1981). *Attention and Self-Regulation: A Control-Theory Approach to Human Behavior*. Springer-Verlag.

[23] Heylighen, F. (2001). A Cybernetic Perspective on the New Science of the Mind. In *Encyclopedia of Cognitive Science*. Wiley.

[24] Packer, C., Wooders, S., Lin, K., Fang, V., Patil, S. G., Stoica, I., & Gonzalez, J. E. (2023). MemGPT: Towards LLMs as Operating Systems. *arXiv preprint arXiv:2310.08560*.

[25] Khattab, O., Santhanam, K., Li, X. L., Hall, D., Liang, P., Potts, C., & Zaharia, M. (2022). Demonstrate-Search-Predict: Composing retrieval and language models for knowledge-intensive NLP. *arXiv preprint arXiv:2212.14024*.

[26] Yao, S., Zhao, J., Yu, D., Du, N., Shafran, I., Narasimhan, K., & Cao, Y. (2023). ReAct: Synergizing Reasoning and Acting in Language Models. *Proceedings of ICLR 2023*.

[27] Madaan, A., Tandon, N., Gupta, P., Hallinan, S., Gao, L., Wiegreffe, S., ... & Clark, P. (2023). Self-Refine: Iterative Refinement with Self-Feedback. *arXiv preprint arXiv:2303.17651*.

[28] Shinn, N., Labash, B., & Gopinath, A. (2023). Reflexion: An Autonomous Agent with Dynamic Memory and Self-Reflection. *arXiv preprint arXiv:2303.11366*.

[29] Penligent Research. (2026). *AI-Agent Sandboxing: A Four-Boundary Model*. White paper.

[30] Docker Inc. (2025). *Docker Sandboxes: Isolation for AI agent workloads*. Product documentation.

[31] Brooks, R. A. (1991). Intelligence Without Representation. *Artificial Intelligence*, 47, 139–159.

[32] Kahneman, D., & Tversky, A. (1979). Prospect Theory: An Analysis of Decision under Risk. *Econometrica*, 47(2), 263–291.

[33] Powers, W. T. (1973). *Behavior: The Control of Perception*. Aldine.

[34] Minsky, M. (1986). *The Society of Mind*. Simon & Schuster.

[35] Russell, S. (2019). *Human Compatible: Artificial Intelligence and the Problem of Control*. Viking.

[36] Christiano, P. F., Leike, J., Brown, T. B., Martic, M., Legg, S., & Amodei, D. (2017). Deep Reinforcement Learning from Human Preferences. In *NeurIPS 2017*.

[37] Bai, Y., Jones, A., Ndousse, K., Askell, A., Chen, A., DasSarma, N., ... & Kaplan, J. (2022). Training a Helpful and Harmless Assistant with Reinforcement Learning from Human Feedback. *arXiv preprint arXiv:2204.05862*.

[38] Bai, Y., Kadavath, S., Kundu, S., Askell, A., Kernion, J., Jones, A., ... & Kaplan, J. (2022). Constitutional AI: Harmlessness from AI Feedback. *arXiv preprint arXiv:2212.08073*.

[39] Anthropic. (2024). *Responsible Scaling Policy v2.0*. https://www.anthropic.com/news/responsible-scaling-policy

[40] Hendrycks, D., Carlini, N., Schulman, J., & Steinhardt, J. (2021). Unsolved Problems in ML Safety. *arXiv preprint arXiv:2109.13916*.

[41] Ha, D., & Schmidhuber, J. (2018). World Models. *arXiv preprint arXiv:1803.10122*.

[42] Hafner, D., Pasukonis, J., Ba, J., & Lillicrap, T. (2023). Mastering Diverse Domains through World Models. *arXiv preprint arXiv:2301.04104*.

[43] AutoGPT Community. (2023–2025). *AutoGPT: An experimental open-source attempt to make GPT-4 fully autonomous*. https://github.com/Significant-Gravitas/AutoGPT

[44] Wang, L., Ma, C., Feng, X., Zhang, Z., Yang, H., Zhang, J., ... & Wen, J.-R. (2024). A Survey on Large Language Model based Autonomous Agents. *Frontiers of Computer Science*, 18(6), 186345.

[45] Xi, Z., Chen, W., Guo, X., He, W., Ding, Y., Hong, B., ... & Huang, X. (2023). The Rise and Potential of Large Language Model Based Agents: A Survey. *arXiv preprint arXiv:2309.07864*.

[46] Park, J. S., O'Brien, J. C., Cai, C. J., Morris, M. R., Liang, P., & Bernstein, M. S. (2023). Generative Agents: Interactive Simulacra of Human Behavior. *Proceedings of UIST 2023*.

[47] Yao, S., Yu, D., Zhao, J., Shafran, I., Griffiths, T. L., Cao, Y., & Narasimhan, K. (2023). Tree of Thoughts: Deliberate Problem Solving with Large Language Models. *NeurIPS 2023*.

---

*End of paper. Version 1.0 — April 2026.*
