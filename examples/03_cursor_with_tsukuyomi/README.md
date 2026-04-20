# Example 03 — Cursor Composer with Tsukuyomi

Cursor Composer proposes a 6-file change. Tsukuyomi catches the scope.

## Configure Cursor

Settings → Models → OpenAI: set "Override Base URL" to `http://localhost:9999`.

## Run

In Cursor Composer:
> "extract the auth logic into a separate module and update all callers"

## What happens

- Skin: Tier 3 (multi-file refactor).
- Shoulders: blast radius HIGH (auth is called from ~11 sites).
- Protocol Gary: audit. Asks Cursor's backing model 5 questions.
- Sandbox: simulates; if the 6 files declared in the plan match the 11 files
  actually modified, match_score = 6/11 = 0.55 → FAIL.
- Mouth: "Sandbox rejected plan; expected 6 files, 11 changed. Approve?"

The human sees exactly which files exceeded scope and can approve or deny.
