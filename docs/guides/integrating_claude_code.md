# Integrating Claude Code with Tsukuyomi

**Audience:** Developers using Claude Code who want safety enforcement.
**Prerequisites:** Claude Code installed; Tsukuyomi running (`installation.md` §7).

---

## 1. The single configuration step

Claude Code respects the `ANTHROPIC_BASE_URL` environment variable. Set it to point at Tsukuyomi:

```bash
export ANTHROPIC_BASE_URL=http://localhost:9999
```

That is the entire integration.

To make this permanent, add the export to `~/.bashrc` or `~/.zshrc`. To use a per-project setting, put it in a `.envrc` if you use direnv.

## 2. Verify

In a fresh terminal:

```bash
claude-code "what is in the README?"
```

In the Tsukuyomi terminal, you should see a request appear in the log stream. From the Tsukuyomi dashboard:

```bash
tsukuyomi dashboard
```

The latest request entry should show `agent_hint=claude-code`.

## 3. What happens now

Every Claude Code session sends its requests through Tsukuyomi. Routine read-only operations (Tier 1) pass through quickly with only Skin classification, Knee check, and Toe budget check. Code-modifying operations (Tier 2/3) trigger Shoulders blast-radius analysis, possibly Protocol Gary forced audit, and possibly the sandbox simulation before the agent's tool call is permitted.

You will notice:

- A small (~10ms) latency increase on every request (the proxy hop).
- Some operations take longer (5–30s extra) when Protocol Gary or the sandbox is engaged. This is the safety machinery doing its job.
- Tsukuyomi's logs (`~/.local/share/tsukuyomi/data/logs/anatomy.jsonl`) record everything for later review.

## 4. Configure Claude Code's API key

Tsukuyomi requires you to provide your Anthropic key via environment variable to *Tsukuyomi*, not to Claude Code:

```bash
# Tsukuyomi-side (this is what reaches Anthropic):
export ANTHROPIC_API_KEY=sk-ant-...

# Claude Code can have a placeholder; Tsukuyomi rewrites it:
export ANTHROPIC_API_KEY_FOR_CLAUDE_CODE=any_value_works
```

Claude Code will read its `ANTHROPIC_API_KEY` and pass it as the `x-api-key` header. Tsukuyomi receives that header, ignores the value (which can be a placeholder), and uses *its own* configured `ANTHROPIC_API_KEY` for the upstream call. This is the credential isolation property described in `02_interceptor.md` §5.2.

If you'd rather pass through the agent's key directly (less safe, but simpler):

```json
"interceptor": {
  "credential_passthrough": true
}
```

## 5. Override per-project

For a specific project that you want to run without Tsukuyomi (e.g., a sandbox/exploration repo where you accept the risk):

```bash
unset ANTHROPIC_BASE_URL
claude-code ...
```

This is reversible; `export ANTHROPIC_BASE_URL=http://localhost:9999` re-engages Tsukuyomi for the next session.

## 6. What Tsukuyomi does NOT do for Claude Code

- It does not modify Claude Code's CLI output.
- It does not change which tools Claude Code has.
- It does not interfere with Claude Code's hooks (you can keep them; they're additive).
- It does not store your Claude Code session history (Claude Code does that locally; Tsukuyomi has its own audit log of *its own* decisions, separate from your conversation transcript).

## 7. Troubleshooting

**Claude Code says "connection refused".** Tsukuyomi is not running on `localhost:9999`. Start it: `tsukuyomi start`.

**Requests succeed but I don't see them in Tsukuyomi.** Check `echo $ANTHROPIC_BASE_URL` — it might not be set in this shell. Re-export.

**Operations are noticeably slower.** Expected on Tier-3 operations (Protocol Gary, sandbox). Check the dashboard to see whether the latency is in your Skin tier (Tier 1 should be fast) — if Tier 1 is also slow, see `troubleshooting.md`.
