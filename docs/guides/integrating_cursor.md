# Integrating Cursor with Tsukuyomi

**Audience:** Cursor IDE users who want safety enforcement.
**Prerequisites:** Cursor installed; Tsukuyomi running.

---

## 1. Cursor's "Custom API endpoint" feature

Cursor supports a custom OpenAI-compatible endpoint in its settings:

1. Open Cursor settings (`Cmd+,` on macOS, `Ctrl+,` on Linux/Windows).
2. Navigate to "Models" → "OpenAI API Settings".
3. Set "Override OpenAI Base URL" to: `http://localhost:9999`
4. Set the API key field to a placeholder (Tsukuyomi rewrites this server-side; see §3 below).
5. Set the model to one that your configured upstream supports (e.g., `gpt-4o`, `claude-3-5-sonnet-20241022`).

For Anthropic mode (Cursor's "Use Custom Anthropic Endpoint"):
- Override URL: `http://localhost:9999`
- The Anthropic API key field gets the placeholder.

Restart Cursor for the settings to take effect.

## 2. Verify

In Cursor, open the chat panel (`Cmd+L`) and send a simple request: "what does this file do?"

Tsukuyomi dashboard should show the request with `agent_hint=cursor` (Cursor's User-Agent is recognizable).

## 3. Credential rewriting

Cursor sends the configured API key in every request. Tsukuyomi captures it, ignores it, and uses its own configured upstream credentials (the `ANTHROPIC_API_KEY` or `OPENAI_API_KEY` Tsukuyomi was started with). The placeholder you set in Cursor's UI is never sent to Anthropic or OpenAI; it terminates at Tsukuyomi.

This is desirable because it means: (a) Cursor's settings file does not contain your real API key, (b) you can rotate your real key without touching Cursor, and (c) Tsukuyomi-side audit logs identify which agent made which call.

## 4. Cursor-specific tuning

Cursor's "Composer" mode generates more aggressive multi-file plans than chat mode. Tsukuyomi's Shoulders are particularly valuable here; the included `config/agents/cursor.json` profile tightens the thresholds:

```json
{
  "extends": "../corelaw.json",
  "organs": {
    "shoulders": {
      "thresholds": {
        "high_max_callers": 10                // tighter than default 15
      }
    }
  }
}
```

Use:

```bash
tsukuyomi start --profile config/agents/cursor.json
```

## 5. Limitations

- Cursor's autocomplete (Tab completion) does not pass through the chat API and is not intercepted by Tsukuyomi. This is by design — autocomplete is read-only and very high-frequency; intercepting it would impose latency without safety value.
- Cursor's "Apply to file" action *is* intercepted (it's a tool call from the chat side).
