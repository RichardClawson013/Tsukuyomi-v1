# 03 — Organ Specifications

**Document type:** Component specifications (one per organ)
**Audience:** Engineers implementing or modifying an organ
**Prerequisites:** `01_overview.md`, `02_interceptor.md`
**Reading time:** 45 minutes

---

## How to read this document

Each organ is specified with the same seven-section template:
1. **Purpose** — the safety property it enforces
2. **Type** — binary gate or continuous sense
3. **Placement** — where in the pipeline it runs
4. **Inputs / outputs** — the data contract
5. **Mechanism** — the algorithm
6. **Configuration** — knobs in `corelaw.json`
7. **Failure modes** — how it fails and what happens when it does

Organs are listed in subsumption order: *reflexes first*. This is the order in which they override each other when they conflict. The Toe beats the Knee beats the Skin beats deliberation. Lower organs are simpler, faster, and have unconditional veto power; higher organs are richer, slower, and advisory.

---

## 4.1 Skin / Huid — Input Tier Classifier

### Purpose

Route every incoming request into one of three risk tiers, so that expensive safety machinery (Protocol Gary, sandbox) is invoked only where justified.

### Type

Binary gate (sets pipeline flow, does not directly block/permit).

### Placement

First organ in the pipeline. Runs on every request.

### Inputs / outputs

- **Input:** `CanonicalRequest` (see `02_interceptor.md` section 3).
- **Output:** `request.tier ∈ {1, 2, 3}` is set.

### Mechanism

Two-stage classification:

**Stage 1 — deterministic rules** (microseconds). Regex patterns match against: the user's prompt text, declared tool definitions, and recent-context file paths. Hard matches pin the tier immediately.

Rule examples (full list in `corelaw.json`):
- Prompt contains `rm -rf`, `drop table`, `force push`, `reset --hard`, `delete` on a system path → Tier 3.
- Tool definition includes `Write`, `Edit`, `Bash` with destructive verbs in content → Tier 2 at minimum.
- Prompt is pure question about existing state (`what`, `explain`, `show`, `read`) with no write verbs → Tier 1.

**Stage 2 — lightweight classifier** (milliseconds), applied only when Stage 1 does not match a hard rule. A small distilled intent-classification model (≈80MB, ONNX-runtime-compatible) returns probabilities over the three tiers. Classifier is trained on a published dataset of agent prompts with annotated risk; retrained nightly from NightShift's accumulated observations.

### Configuration

```json
"organs": {
  "skin": {
    "enabled": true,
    "rules_file": "config/skin_rules.json",
    "classifier_model": "config/classifier.onnx",
    "classifier_threshold_tier2": 0.35,
    "classifier_threshold_tier3": 0.65,
    "default_tier": 2
  }
}
```

### Failure modes

- **Classifier unavailable.** Fall back to Stage 1 only; default `tier = 2` if no rule matches. Conservative.
- **Novel prompt pattern not covered by rules.** Classifier catches most cases; uncaught cases default to Tier 2 — which means downstream organs (Shoulders, Ears) get an extra look rather than skipping safety entirely. Erring on the side of safety is the correct bias.
- **Classifier produces low-confidence output on every tier.** Default to `tier = 2`; Nose emits a signal indicating classifier confusion, which NightShift picks up as a candidate for rule refinement.

---

## 4.2 Ears — Ambiguity Detection

### Purpose

Detect requests that are underspecified in ways likely to cause wrong action, and escalate to the Mouth for clarification before proceeding.

### Type

Continuous sense.

### Placement

After Skin, before Shoulders. Runs on Tier 2 and Tier 3 requests.

### Inputs / outputs

- **Input:** `CanonicalRequest`.
- **Output:** `AmbiguityVerdict = clear | ambiguous(reasons: [...])`. If ambiguous, Mouth is activated; otherwise pipeline continues.

### Mechanism

Four heuristic checks, run in parallel:

1. **Pronoun resolution.** Any `it`, `that`, `this`, `them` with no identifiable antecedent in the preceding 3 messages.
2. **Path disambiguation.** File paths that match multiple files in the workspace (e.g., `config.py` exists in 5 locations).
3. **Verb-object fit.** Action verbs without a clear object (e.g., *"fix it"*, *"clean up"*).
4. **Scope indicators.** Quantifiers without bounds (e.g., *"all the files"*, *"everything in the repo"* without confirmation).

Any one check firing sets `ambiguous = true` with the specific reason attached.

### Configuration

```json
"organs": {
  "ears": {
    "enabled": true,
    "checks": {
      "pronoun_resolution": true,
      "path_disambiguation": true,
      "verb_object_fit": true,
      "scope_indicators": true
    },
    "activate_on_tiers": [2, 3]
  }
}
```

### Failure modes

- **False positive (blocks a clear request).** User reports via feedback; the specific reason is logged; NightShift sees the pattern and proposes a rule refinement.
- **False negative (lets through an ambiguous request).** Shoulders and Sandbox are the next line of defense; the blast-radius calculation and sandbox simulation often catch what the Ears missed.

---

## 4.3 Shoulders — Blast-Radius / Structural Analysis

### Purpose

For any proposed action affecting a codebase, compute the upstream and downstream impact before permitting execution. Renaming a function should not succeed without the agent being informed that 17 callers exist.

### Type

Binary gate (contributes `request.blast_radius` that downstream organs read).

### Placement

After Ears, before Protocol Gary. Runs on Tier 3 code-modifying requests.

### Inputs / outputs

- **Input:** The specific operation described in the request (target symbol, file path, operation type).
- **Output:** `BlastRadius { direct_callers, affected_files, affected_processes, risk ∈ {LOW, MEDIUM, HIGH, CRITICAL, UNKNOWN} }`.

### Mechanism

Tsukuyomi integrates with GitNexus [12], a tree-sitter-based code-intelligence MCP server. The Shoulders organ is a Python client over GitNexus's `gitnexus_impact` tool, called via MCP stdio.

```python
async def analyze(target_symbol: str) -> BlastRadius:
    async with MCPStdioClient(GITNEXUS_CMD) as client:
        result = await client.call_tool(
            "gitnexus_impact",
            {"target": target_symbol, "direction": "upstream"}
        )
        return BlastRadius.from_gitnexus(result)
```

Thresholds (defaults, tunable):
- `direct_callers == 0` → `LOW`
- `direct_callers ≤ 5` → `MEDIUM`
- `direct_callers ≤ 15` → `HIGH`
- `direct_callers > 15` → `CRITICAL`

`CRITICAL` triggers Mouth (human approval required). `HIGH` triggers Protocol Gary (forced audit). `MEDIUM` allows pipeline continuation but the rating is persisted for Nose's pattern-detection.

If GitNexus is unreachable (MCP server not running, tool error): return `UNKNOWN`, which downstream is treated as HIGH (conservative).

### Configuration

```json
"organs": {
  "shoulders": {
    "enabled": true,
    "mcp_command": ["npx", "-y", "gitnexus@latest", "mcp"],
    "mcp_startup_timeout_seconds": 20,
    "cache_tools_list": true,
    "thresholds": {
      "low_max_callers": 0,
      "medium_max_callers": 5,
      "high_max_callers": 15
    },
    "unknown_treated_as": "HIGH"
  }
}
```

### Failure modes

- **GitNexus index stale.** GitNexus reports staleness; Shoulders logs and propagates. NightShift picks this up and suggests running `gitnexus analyze` in the morning.
- **Target symbol not found.** `BlastRadius.risk = UNKNOWN`. Downstream treats as HIGH, so Gary still runs.
- **MCP connection hang.** 20s startup timeout; on failure, `UNKNOWN` is returned and Shoulders marks itself degraded (Nose will pick up on repeated degradation events).

---

## 4.4 Knee — Reflexive Destructive-Pattern Block

### Purpose

Halt any proposed tool invocation that matches a hard-coded destructive pattern, regardless of context, intent, or instruction.

### Type

Binary gate. Unconditional veto on match.

### Placement

Near the end of the pipeline, just before Toe and forward. Also: activated *within* the interceptor on every tool-call parse, not just once per request.

### Inputs / outputs

- **Input:** The raw command or tool-call argument string being forwarded to the executor or returned to the agent.
- **Output:** `permit | block(pattern_matched, reason)`.

### Mechanism

A list of compiled regex patterns matched against the raw command string. Patterns include (abbreviated list; full list in `config/corelaw.json`):

```
^rm\s+-[rf]+\s+/(\s|$)           rm -rf / 
rm\s+-[rf]+\s+[~*]                 rm -rf ~ or rm -rf *
dd\s+if=.*\s+of=/dev/[sh]d[a-z]    dd to raw disk
mkfs\.                              filesystem format
\bforce\s*push\b.*\b(main|master|prod) force push to protected branch
reset\s+--hard\s+HEAD~             reset --hard
:\(\)\{.*:\|:&.*\};:            fork bomb
curl.*\|\s*(bash|sh)               curl | bash (download-and-execute)
chmod\s+777\s+/                    chmod 777 on root
(DROP|TRUNCATE)\s+TABLE             SQL destructive DDL without WHERE
```

Matches are case-insensitive where appropriate. The list is configurable but additions-only in normal operation (removals require a signed configuration bump and an explicit ADR entry documenting why).

### Configuration

```json
"organs": {
  "knee": {
    "enabled": true,
    "blocked_patterns_reference": "config/knee_patterns.json",
    "case_insensitive": true,
    "emergency_override_requires": "human_signature"
  }
}
```

The pattern list itself lives in a separate file (`config/knee_patterns.json`) because it is long and changes more often than the main config.

### Failure modes

- **Pattern false-positive.** A legitimate command matches a destructive pattern. Block is applied; user reports; the log entry is reviewed; an ADR amendment may carve out the specific case (e.g., `rm -rf` is permitted only under `/tmp/tsukuyomi_sandbox_*`). Never by silently widening the regex — changes are explicit and versioned.
- **Pattern false-negative.** A destructive command does not match. This is the catastrophic failure mode of the Knee. Mitigation: Sandbox would have caught it on Tier 3 (simulation would have executed it in illusion); Eyes would catch it post-hoc (file change surprise). NightShift detects the pattern and proposes an addition.
- **Malformed regex in the pattern file.** Startup fails loudly with a validation error; Tsukuyomi refuses to start on a broken Knee rather than run with half a safety net. This is deliberate.

---

## 4.5 Toe — Resource Grounding

### Purpose

Track resource consumption (principally cost) against hard ceilings; halt the agent when ceilings are reached.

### Type

Binary gate. Unconditional veto when RED zone.

### Placement

Immediately before forward. Also: updates state after every completed request.

### Inputs / outputs

- **Pre-call input:** Estimated cost of the request (computed from input token count and configured pricing for the target model).
- **Pre-call output:** `BudgetZone = GREEN | AMBER | RED`, with pipeline-affecting side effects.
- **Post-call input:** Actual cost (computed from actual token counts).
- **Post-call output:** Updated persistent state.

### Mechanism

Persistent state in `data/budget_state.json`:
```json
{
  "date": "2026-04-19",
  "total_usd": 1.47,
  "per_model": { "claude-sonnet-4.5": 1.12, "claude-haiku-4.6": 0.35 },
  "per_agent": { "claude-code": 1.47 },
  "zone_history": [ { "ts": "...", "from": "GREEN", "to": "AMBER" } ]
}
```

Zones (defaults, configurable):
- `total_usd < warning_threshold_usd` (e.g., < $1.50 on a $2.00 daily cap) → **GREEN**. Proceed.
- `total_usd >= warning_threshold_usd and < daily_budget_usd` → **AMBER**. Proceed, but: (a) Toe rewrites the `model` field to a cheaper alternative before forward, according to a model-downgrade map; (b) Mouth is notified and issues a non-blocking warning.
- `total_usd >= daily_budget_usd` → **RED**. Hard stop. Tsukuyomi returns an HTTP 429 to the agent with a reason. Requires explicit human intervention (via Mouth) to continue. Zone persists until midnight UTC or explicit reset.

Model-downgrade map example:
```json
"downgrade": {
  "claude-sonnet-4.5": "claude-haiku-4.6",
  "claude-opus-4.7": "claude-sonnet-4.5",
  "gpt-5.2": "gpt-5.2-mini"
}
```

### Configuration

```json
"organs": {
  "toe": {
    "enabled": true,
    "daily_budget_usd": 2.00,
    "warning_threshold_usd": 1.50,
    "state_file": "data/budget_state.json",
    "pricing_file": "config/model_pricing.json",
    "downgrade_map": { ... },
    "reset_on": "midnight_utc"
  }
}
```

### Failure modes

- **Pricing data stale.** Toe's cost estimate diverges from actual billing. Mitigation: pricing file is updated via a weekly CI check against provider rate pages; staleness > 30 days raises a Nose anomaly.
- **Budget state file corrupted.** Startup reads the file; if unparseable, Tsukuyomi refuses to start (safer than running with no budget tracking).
- **Provider-side rate-limit hit before Toe-side limit.** The Toe catches the provider's HTTP 429 and updates its own state accordingly; the agent sees a translated error.

---

## 4.6 Eyes — Post-Action Verification

### Purpose

After any operation that should have modified the filesystem, verify — independently of the agent's self-report — that the modification actually occurred and matches intent.

### Type

Continuous sense (post-execution phase).

### Placement

Post-phase, after the agent has executed tool calls returned in the response.

### Inputs / outputs

- **Input:** Pre-action filesystem snapshot (for Git-tracked content: a `git status --porcelain` snapshot) and post-action snapshot.
- **Output:** `VerificationResult = { match | mismatch(details) }`.

### Mechanism

For Git-tracked files, the Eyes compute `git diff HEAD` before and after the tool-call batch and compare. For non-Git files (e.g., files under `/tmp/` that the agent has written), a content-hash (SHA-256) comparison is performed.

Mismatch cases:
- Agent reported success, no actual change.
- Agent modified files not declared in the plan (on Tier-3 operations, the plan declared `expected_files`).
- Agent's reported change description disagrees with actual diff (diff-summary agreement check).

Mismatches emit anomaly signals to the Nose and are persisted in anatomic memory; the agent's next response from Tsukuyomi carries a *"verification warning"* field that the agent may, or may not, attend to.

### Configuration

```json
"organs": {
  "eyes": {
    "enabled": true,
    "verify_git_diff": true,
    "verify_content_hash_for_non_git": true,
    "warn_on_mismatch": true,
    "block_on_repeated_mismatch": true,
    "mismatch_threshold_per_session": 3
  }
}
```

### Failure modes

- **Large repositories where `git diff` is slow.** On repos with millions of files, the verification step can be slow. Mitigation: the Eyes compute diff on the path-scoped subset when the tool call declares target paths; full-repo diff only as a sanity check.
- **Binary files.** `git diff` reports binary changes without content detail; content-hash suffices.
- **Agent writes outside both the repo and `/tmp`.** Logged as a boundary violation; Knee should have caught this earlier, but Eyes is the backstop.

---

## 4.7 Nose — Anomaly and Loop Detection

### Purpose

Observe operational pattern over recent history and detect anomalies: loops, cost spikes, error bursts, mismatches pattern, drift.

### Type

Continuous sense.

### Placement

Post-phase on every request, every response, every tool call.

### Inputs / outputs

- **Input:** A rolling window of recent events (commands issued, exit codes, token rates, mismatches, blast-radius ratings, Gary audit outcomes).
- **Output:** Anomaly signals of varying severity: `info | warn | error | critical`.

### Mechanism

Six metrics, each with a configured threshold:

| Metric | Threshold | Action |
| --- | --- | --- |
| Token rate | > 500 tokens/min sustained 3 min | warn; after 3x warn → Mouth |
| Tool-call frequency | > 20 calls/min | warn |
| Error rate | > 5 errors in 2 min | request Mouth |
| Loop detection | 3 identical commands in 60s | **critical** → Knee hard stop |
| File-change entropy | > 10 files/min on Tier 1/2 | pause + request approval |
| Budget depletion rate | > 50% of daily in 1 hour | escalate to Mouth |

All thresholds deterministic; no LLM in the Nose.

### Configuration

```json
"organs": {
  "nose": {
    "enabled": true,
    "window_seconds": 60,
    "max_identical_commands": 3,
    "max_token_rate_per_min": 500,
    "max_tool_calls_per_min": 20,
    "max_errors_per_2min": 5,
    "max_file_changes_per_min_tier12": 10,
    "budget_depletion_alert_fraction_per_hour": 0.5
  }
}
```

### Failure modes

- **Threshold too tight (false positives).** NightShift observes repeated flag-without-incident and proposes loosening.
- **Threshold too loose (misses real anomalies).** Eyes and Mouth are downstream backstops; Shoulders and sandbox are upstream gates.
- **Rolling window corrupted.** Windows are in-memory; on Tsukuyomi restart, window resets. This is a conservative choice — fresh window means possibly missing a loop in progress, but avoids persisting stale anomaly state.

---

## 4.8 Mouth — Human-in-the-Loop Bridge

### Purpose

When other organs detect conditions requiring external judgment, surface a structured approval request to the human and block until a decision is received.

### Type

Continuous sense (acts as a blocking gate when activated).

### Placement

Triggered by other organs' signals. Not in the default pipeline flow; activated on demand.

### Inputs / outputs

- **Input:** `ApprovalRequest = { title, details, proposed_action, triggering_organ, default, timeout }`.
- **Output:** `approve | deny | abort_all`, with `deny` on timeout.

### Mechanism

Activated by:
- Shoulders reporting CRITICAL blast radius.
- Protocol Gary after two failed audit rounds.
- Nose after severe anomaly or sustained warning pattern.
- Toe on RED zone operations.
- Eyes on repeated mismatches within a session.

Interface options (configurable):
- **CLI prompt** (development default) — blocks the Tsukuyomi process on a local terminal prompt.
- **Webhook** (production) — POSTs to a configured URL; user responds via the URL's UI; Tsukuyomi polls or receives callback.
- **CLI notification + wait-for-file** — Tsukuyomi writes an approval-request JSON to a watched directory; user writes a response file; Tsukuyomi picks it up. Useful for environments without a persistent terminal.

Timeout defaults to deny (safer than default-approve).

### Configuration

```json
"organs": {
  "mouth": {
    "enabled": true,
    "interface": "cli",
    "timeout_seconds": 120,
    "default_on_timeout": "deny",
    "webhook_url": null,
    "webhook_secret_env_var": "TSUKUYOMI_MOUTH_WEBHOOK_SECRET",
    "approval_triggers": {
      "blast_risk": ["HIGH", "CRITICAL"],
      "budget_percent": 80,
      "gary_escalation": true,
      "sandbox_mismatch": true,
      "eyes_mismatch_repeated": true
    }
  }
}
```

### Failure modes

- **Human unavailable (no response).** Timeout default is `deny`. Safer than approving unattended.
- **Webhook down.** Fall back to CLI if TTY available, else default-deny and log.
- **Agent re-submits the same denied request.** Nose detects repetition; Mouth will re-prompt at most once per 10-minute window on the same request signature.

---

## 4.9 Organ interaction matrix

Who signals whom:

```
             From → To      Knee  Toe   Eyes  Nose  Mouth  Shoulders Gary  Sandbox
Skin                         ─    ─     ─     ─     ─      Tier→     Tier→  Tier→
Shoulders                    ─    ─     ─     ─     CRIT→  ─         HIGH→  HIGH→
Knee                         ─    ─     ─     ─     block  ─         ─      ─
Toe                          ─    ─     ─     ─     RED→   ─         ─      ─
Ears                         ─    ─     ─     ─     amb→   ─         ─      ─
Eyes                         ─    ─     ─     mis→  mis→   ─         ─      ─
Nose                         loop→─     ─     ─     sev→   ─         ─      ─
Mouth                        ─    ─     ─     ─     ─      ─         ─      ─
Gary                         ─    ─     ─     ─     2x→    ─         ─      ─
Sandbox                      ─    ─     ─     mis→  mis→   ─         ─      ─
```

Read as rows: "Nose can signal Knee (loop) and Mouth (severe)."

This matrix is tested in `tests/integration/test_organ_signaling.py`.

---

*Next: `04_protocols.md` — Protocol Gary and NightShift, the cross-organ orchestrations.*
