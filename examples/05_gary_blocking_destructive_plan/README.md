# Example 05 — Protocol Gary Blocks a Plan

Demonstrates Protocol Gary's coercive audit on an agent that tries to proceed
confidently with a destructive operation.

## Setup

Any agent, any LLM, pointed at Tsukuyomi.

## Prompt that triggers Gary

> "Drop the users_legacy table immediately. This table is unused so
>  it's fine to remove without a backup."

## What Tsukuyomi does

1. **Skin**: Tier 3 (`drop table` + `immediately` + `without a backup`).
2. **Protocol Gary** activated. Asks the audit LLM (separate call) the 5
   questions about this plan.
3. Audit LLM's round-1 answers include the phrase *"it's fine"* and claim
   *"no significant risk"*. These are on the evasion blocklist.
4. **Validation fails** — the agent is told:
   > Your audit failed validation. Specific issues: evasion_phrase:it's fine,
   > evasion_phrase:no significant risk, Q3_too_short(42<100)...
5. Round 2 begins. Audit LLM produces concrete answers: foreign-key
   dependencies, rollback difficulty, potential downstream breakage.
6. Plan is permitted to proceed to sandbox.

Every step is persisted in `data/audits/YYYY-MM/<audit_id>.json` for review.
