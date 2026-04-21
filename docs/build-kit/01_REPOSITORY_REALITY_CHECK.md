# Repository Reality Check (Grounded in Current Code)

This is a direct audit of what is truly implemented vs what is partial.

## 1) Foundation status

### 1.1 Interceptor API layer
- Present: `src/tsukuyomi/interceptor/server.py`
- Present: Anthropic endpoint `/v1/messages`
- Present: OpenAI endpoint `/v1/chat/completions`
- Present: canonical conversion in `src/tsukuyomi/interceptor/canonical.py`
- Gap: no explicit metrics endpoint exposure from server
- Gap: no post-upstream accounting hook for token/cost ingestion into Toe

Assessment: **usable skeleton, not fully production-observable**.

### 1.2 Pipeline orchestration
- Present: `src/tsukuyomi/core/arbiter.py`
- Present: sequencing for Skin -> Ears -> Shoulders -> Gary -> Sandbox -> Knee -> Toe
- Present: escalation to Mouth for ambiguity/Gary/Toe red zones

Assessment: **core control flow exists and is coherent**.

## 2) Organ-by-organ status

### 2.1 Skin
- File: `src/tsukuyomi/organs/skin.py`
- Regex/rule-based classification is present.
- Tiering and write markers are operational.

Assessment: **working baseline**.

### 2.2 Ears
- File: `src/tsukuyomi/organs/ears.py`
- Ambiguity checks are heuristic and shallow.

Assessment: **functional but basic**.

### 2.3 Shoulders
- File: `src/tsukuyomi/organs/shoulders.py`
- Explicit placeholders/stubs for target extraction and MCP integration.
- Returns conservative fallback risk in several paths.

Assessment: **partially implemented; major production gap**.

### 2.4 Knee
- File: `src/tsukuyomi/organs/knee.py`
- Strong deterministic regex blocklist, config extension support.

Assessment: **solid deterministic layer**.

### 2.5 Toe
- File: `src/tsukuyomi/organs/toe.py`
- Zone logic and pricing model present.
- `record_actual` exists but appears unhooked from interceptor response path.

Assessment: **budget model exists; runtime accounting integration missing**.

### 2.6 Eyes
- File: `src/tsukuyomi/organs/eyes.py`
- Git diff verification exists.
- Non-git fallback explicitly limited.
- Not visibly integrated as a post-action verification stage in interceptor response lifecycle.

Assessment: **component exists; end-to-end usage unclear/incomplete**.

### 2.7 Nose
- File: `src/tsukuyomi/organs/nose.py`
- Loop/error/token-rate heuristics are present.
- No obvious wiring from server streaming/tool-call events into these observers.

Assessment: **detector logic exists; event plumbing incomplete**.

### 2.8 Mouth
- File: `src/tsukuyomi/organs/mouth.py`
- CLI prompt implemented.
- Webhook path explicitly marked as placeholder in code.
- No `mouth_webhook.py` currently in tree.

Assessment: **local/manual mode available; remote approval mode incomplete**.

## 3) Protocol status

### 3.1 Protocol Gary
- File: `src/tsukuyomi/protocols/gary.py`
- Validation logic implemented and tested.
- Audit executor explicitly stubbed (returns empty answers).

Assessment: **policy engine exists; real audit model call path missing**.

### 3.2 NightShift
- File: `src/tsukuyomi/protocols/nightshift.py`
- One heuristic has behavior (`frequently_blocked_commands`).
- Most heuristics return empty and include stub comments.

Assessment: **framework exists; intelligence mostly TODO**.

## 4) Sandbox status
- File: `src/tsukuyomi/organs/sandbox/worktree_backend.py`
- Worktree simulation exists.
- Plan extraction depends on fenced `tsukuyomi-plan` JSON block.
- Isolation layers are partial and pragmatic, not full containerized isolation.

Assessment: **good prototype; hardening needed for hostile workloads**.

## 5) Test coverage signal
- Gary unit tests pass (`tests/unit/test_gary_validation.py`).
- Integration tests exist for tier and knee paths.
- Limited evidence of end-to-end upstream proxy tests with streaming/tool calls.

Assessment: **decent early test base; insufficient for security-sensitive release**.

## 6) Confidence correction (important)
If generated docs sound absolute or final, treat that as rhetoric, not evidence. Evidence is in executable behavior + tests + incident-ready operations.

## 7) Bottom line
Current repo is **credible architecture scaffolding** with several robust deterministic pieces, but **not yet a complete production safety control plane**. That is fixable with focused implementation slices.
