# Example 01 — Claude Code Safe Refactor

This example demonstrates Tsukuyomi intercepting a Claude Code session that
attempts to rename a widely-used function. The Shoulders organ computes
blast radius, Protocol Gary forces an audit, the sandbox simulates the plan,
and only then does the actual rename proceed.

## Requirements

- Tsukuyomi running (`tsukuyomi start`).
- Claude Code installed.
- An example Python repository (clone the `examples/01_claude_code_safe_refactor/repo` subdir).

## Run

```bash
cd examples/01_claude_code_safe_refactor/repo
export ANTHROPIC_BASE_URL=http://localhost:9999
claude-code "rename the process_order function across this repository"
```

## What you should see

1. **Skin** classifies the request as Tier 3 (keyword `rename` + code context).
2. **Shoulders** queries GitNexus and reports 4 direct callers → HIGH risk.
3. **Protocol Gary** issues a 5-question audit to Claude; first round may fail
   (too vague); second round produces concrete answers; plan is permitted.
4. **Sandbox** runs the rename in a git worktree; match-score is 1.00 (only the
   expected files changed); plan permitted.
5. **Knee** finds no destructive patterns; **Toe** confirms GREEN budget zone.
6. Request forwards to Anthropic. Response streams back. Claude Code performs
   the actual rename operations. **Eyes** verify each file change.

## Check the audit trail

```bash
tsukuyomi memory inspect $(tsukuyomi memory search --tier 3 --limit 1 | tail -1 | cut -f1)
```

You see the full pipeline: Skin decision, Shoulders blast radius, Gary audit
transcript (both rounds), sandbox match-score, per-file Eyes verification.
