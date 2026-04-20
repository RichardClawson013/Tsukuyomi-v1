# Configuration Reference

**Audience:** Anyone tuning Tsukuyomi for their workload.
**Prerequisites:** Installation done.
**Reference scope:** Every field in `corelaw.json` and the referenced sub-files, with defaults and effects.

---

## 1. File layout

```
~/.local/share/tsukuyomi/config/
├── corelaw.json                  Main config
├── knee_patterns.json            Regex blocklist for the Knee organ
├── gary_evasion_phrases.json     Phrases that fail Protocol Gary validation
├── gary_risk_keywords.json       Vocabulary the audit must use
├── model_pricing.json            Per-model cost table for the Toe organ
└── agents/                       Per-agent profile overrides
    ├── claude_code.json
    ├── hermes.json
    └── cursor.json
```

The `extends` field in any profile inherits from the parent file and overrides specific keys.

## 2. corelaw.json — top level

```json
{
  "schema_version": 1,
  "version_label": "1.0.0",
  "interceptor": { ... },
  "upstream": { ... },
  "organs": { ... },
  "protocols": { ... },
  "memory": { ... },
  "observability": { ... }
}
```

## 3. Interceptor section

```json
"interceptor": {
  "host": "127.0.0.1",
  "port": 9999,
  "credential_passthrough": false,
  "require_client_token": false,
  "client_tokens_env_var": "TSUKUYOMI_CLIENT_TOKENS",
  "stream_pass_through": true,
  "max_inbound_size_bytes": 10485760,
  "request_timeout_seconds": 600
}
```

| Key | Effect | Default |
| --- | --- | --- |
| `host` | Bind interface | `127.0.0.1` (localhost only; safer than `0.0.0.0`) |
| `port` | Listen port | `9999` |
| `credential_passthrough` | If true, forwards the agent's `Authorization` header to upstream as-is. If false, Tsukuyomi uses its own configured upstream creds and ignores the agent's. | `false` |
| `require_client_token` | If true, rejects requests without a valid `X-Tsukuyomi-Client-Token`. | `false` |
| `stream_pass_through` | Preserve SSE streaming | `true` |
| `max_inbound_size_bytes` | Reject larger requests | 10 MB |

## 4. Upstream section

```json
"upstream": {
  "default": "anthropic",
  "anthropic": {
    "base_url": "https://api.anthropic.com",
    "api_key_env_var": "ANTHROPIC_API_KEY",
    "default_model": "claude-sonnet-4.5",
    "timeout_seconds": 300
  },
  "openai": {
    "base_url": "https://api.openai.com",
    "api_key_env_var": "OPENAI_API_KEY",
    "default_model": "gpt-4o"
  },
  "openrouter": {
    "base_url": "https://openrouter.ai/api/v1",
    "api_key_env_var": "OPENROUTER_API_KEY"
  },
  "ollama_local": {
    "base_url": "http://localhost:11434",
    "api_key_env_var": null
  }
}
```

The `default` is used when the request's `model` doesn't match any explicitly-routed provider. Routing rules (per-model → provider) can be set in `upstream.routing`:

```json
"upstream": {
  "routing": {
    "claude-*": "anthropic",
    "gpt-*": "openai",
    "qwen-*": "openrouter",
    "llama-*": "ollama_local"
  }
}
```

## 5. Organs section

Each organ has its own object. Common fields:

```json
"organs": {
  "<organ_name>": {
    "enabled": true,
    ...organ-specific fields per docs/architecture/03_organs.md
  }
}
```

Disabling an organ via `"enabled": false` skips it in the pipeline. Disabling Skin or Knee is **not recommended**; Tsukuyomi will emit a startup warning.

### 5.1 Shoulders (GitNexus MCP) fields

`organs.shoulders` controls blast-radius lookups through GitNexus MCP.

```json
"organs": {
  "shoulders": {
    "enabled": true,
    "mcp_command": ["npx", "-y", "gitnexus@latest", "mcp"],
    "mcp_startup_timeout_seconds": 20,
    "thresholds": {
      "low_max_callers": 0,
      "medium_max_callers": 5,
      "high_max_callers": 15
    },
    "unknown_treated_as": "HIGH"
  }
}
```

- `mcp_command`: command used to start the MCP server over stdio.
- `mcp_startup_timeout_seconds`: startup + call timeout budget for MCP JSON-RPC.
- `thresholds`: maps direct-caller counts to LOW/MEDIUM/HIGH/CRITICAL.
- `unknown_treated_as`: fallback risk when MCP is unavailable or parsing fails.

## 6. Protocols section

```json
"protocols": {
  "gary": { ... per docs/architecture/04_protocols.md §5.1 },
  "nightshift": { ... per docs/architecture/04_protocols.md §5.2 }
}
```

### 6.1 Gary audit HTTP executor fields

When `protocols.gary.audit_http_base_url` is set, Gary uses a real HTTP audit model
instead of the deterministic stub.

```json
"protocols": {
  "gary": {
    "audit_http_base_url": "https://api.openai.com/v1",
    "audit_http_api_key_env_var": "OPENAI_API_KEY",
    "audit_http_model": "gpt-4o-mini",
    "audit_timeout_seconds": 20,
    "audit_max_retries": 1,
    "audit_temperature": 0.0,
    "audit_input_per_million_usd": 0.15,
    "audit_output_per_million_usd": 0.60,
    "fallback_audit_http_base_url": "https://openrouter.ai/api/v1",
    "fallback_audit_http_api_key_env_var": "OPENROUTER_API_KEY",
    "fallback_audit_http_model": "anthropic/claude-3.5-haiku"
  }
}
```

If `audit_http_base_url` is omitted/null, Gary stays in safe stub mode and escalates on
validation failure.

## 7. Memory section

```json
"memory": {
  "backend": "sqlite_fts5",
  "sqlite_path": "data/memory.db",
  "wal_mode": true,
  "retention_days_events": 365,
  "retention_days_audits": 365,
  "retention_days_proposals_rejected": 180,
  "retain_message_bodies": false,
  "retain_tool_call_args": false,
  "encrypt_bodies_at_rest": true
}
```

## 8. Observability section

```json
"observability": {
  "log_level": "info",
  "log_dir": "data/logs",
  "log_rotation": "daily",
  "log_retention_days": 365,
  "metrics_enabled": false,
  "metrics_port": 9100,
  "metrics_path": "/metrics",
  "tracing_enabled": false,
  "tracing_sampling": {
    "tier_1": 0.01,
    "tier_2": 0.1,
    "tier_3": 1.0
  }
}
```

## 9. Validating a config

```bash
tsukuyomi config validate                      # validates current
tsukuyomi config validate --file my_config.json  # validates a specific file
tsukuyomi config show                           # prints effective config (with defaults filled in)
tsukuyomi config diff <file>                    # shows what differs from defaults
```

## 10. Reloading a config

Some changes (Knee patterns, Gary phrases) reload on SIGHUP without restart:

```bash
kill -HUP $(cat ~/.local/share/tsukuyomi/run/tsukuyomi.pid)
```

Other changes (interceptor port, upstream URLs) require restart.
