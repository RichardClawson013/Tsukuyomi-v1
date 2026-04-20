# Integrating Hermes Agent with Tsukuyomi

**Audience:** Developers using Hermes Agent (Nous Research) and want safety enforcement.
**Prerequisites:** Hermes installed; Tsukuyomi running (`installation.md` §7).

---

## 1. Why Hermes is a primary integration target

Hermes Agent is a relatively new entrant in the LLM-agent space, designed for high autonomy and trained on the open-weight Hermes-4 family. Open-weight models exhibit higher rates of malformed tool calls (~32% on first attempt for some open-weight checkpoints), which makes the Skin and Knee organs especially valuable. Tsukuyomi was developed in part with Hermes deployments in mind.

## 2. Configuration

Hermes uses the OpenAI Chat Completions wire format. Configure the base URL:

**If Hermes is configured via env var:**
```bash
export OPENAI_BASE_URL=http://localhost:9999
```

**If Hermes uses its own config file:**
```yaml
# hermes config (typical path: ~/.config/hermes/config.yaml)
api:
  base_url: http://localhost:9999
  format: openai
```

**If Hermes is invoked programmatically:**
```python
from hermes import HermesAgent
agent = HermesAgent(api_base="http://localhost:9999")
```

## 3. Tsukuyomi configuration for Hermes

A profile is provided at `config/agents/hermes.json` with tuned thresholds for Hermes characteristics:

```json
{
  "extends": "../corelaw.json",
  "organs": {
    "skin": {
      "classifier_threshold_tier3": 0.55     // tighter than default 0.65
    },
    "knee": {
      // Hermes is more likely to emit malformed shell snippets
      "case_insensitive": true
    },
    "ears": {
      "checks": {
        "verb_object_fit": true              // critical for open-weight
      }
    }
  },
  "protocols": {
    "gary": {
      "fallback_audit_endpoint": "openrouter/anthropic/claude-haiku-4.6"
      // audit Hermes plans with Claude family for cross-family independence
    }
  }
}
```

Apply with:

```bash
tsukuyomi start --profile config/agents/hermes.json
```

## 4. Recommended upstream

Hermes works well against the Hermes-4 405B served via OpenRouter. Configure Tsukuyomi's upstream:

```json
"upstream": {
  "default": "openrouter",
  "openrouter": {
    "base_url": "https://openrouter.ai/api/v1",
    "default_model": "nousresearch/hermes-4-405b"
  }
}
```

The Toe will rewrite this to `nousresearch/hermes-4-70b` in AMBER zone.

## 5. Verify

Run a Hermes session and watch:

```bash
hermes "list the files in this directory"
```

Tsukuyomi dashboard should show the request with `inbound_format=openai`, `agent_hint=hermes` (if Hermes sets a User-Agent that Tsukuyomi recognizes).

## 6. Note on hermes-specific tools

Hermes's tool definitions occasionally include a `description` field with embedded markdown. Tsukuyomi's parser handles this correctly. If you see parse errors in the Tsukuyomi log, file an issue with the request payload (with redaction).
