# Threat model (plain version)

If you only read one line, read this one:

**Tsukuyomi lowers risk by forcing an agent through checks it can't bypass on
that network path. It does not make all risk disappear.**

This file explains what we're defending, what assumptions that defense relies
on, and what can still go wrong.

## 1) What sits inside the boundary

Tsukuyomi is the proxy between:

- your agent, and
- the model provider API.

So the protected surface is mostly:

- repo/filesystem integrity,
- provider credentials,
- budget controls,
- decision/audit trail integrity.

## 2) Who/what the threats are

Not movie villains. Mostly this:

- bad prompts that pressure destructive actions,
- agent loops that keep digging,
- human misconfiguration,
- webhook response tampering/replay.

What this is **not** designed to solve:

- already-compromised host at root level.

## 3) Assumptions this whole thing depends on

- traffic actually goes through Tsukuyomi (no bypass side-path),
- host/runtime is sane enough to trust,
- webhook secret stays secret,
- external dependencies (like GitNexus) can fail, and when they fail we fall
  back conservatively.

If those assumptions are false, safety degrades. Sometimes hard.

## 4) Threats and how Tsukuyomi answers them

### A) Destructive actions

**Threat:** agent proposes dangerous commands/edits.

**Controls:** Skin + Knee + Gary + sandbox + Eyes + Mouth escalation.

**Residual risk:** unknown patterns and semantic edge cases always exist.

### B) Control-plane bypass

**Threat:** agent talks directly to provider.

**Control:** deployment/network setup must force one path through Tsukuyomi.

**Residual risk:** config mistakes can reopen bypass.

### C) Cost runaway

**Threat:** loops burn tokens/budget.

**Control:** Toe zones + downgrade + usage accounting.

**Residual risk:** streaming accounting still less complete than non-stream.

### D) Approval spoof/replay

**Threat:** forged or replayed webhook approval response.

**Control:** HMAC signature + timestamp skew checks + nonce replay guard.

**Residual risk:** current replay memory is process-local (resets on restart).

### E) External analysis unavailable

**Threat:** GitNexus/other external source unavailable.

**Control:** conservative fallback risk (`unknown_treated_as`).

**Residual risk:** more false positives and more human friction.

## 5) Non-goals (explicit)

- Full defense against host compromise.
- Zero false positives.
- Perfect intent understanding.

## 6) Practical hardening moves

- run Tsukuyomi in a dedicated runtime boundary,
- keep outbound network tight,
- rotate webhook secrets,
- periodically review Knee/Gary configs,
- keep `KNOWN_LIMITATIONS.md` honest and up to date.

