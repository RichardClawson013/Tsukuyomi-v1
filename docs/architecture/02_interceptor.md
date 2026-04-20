# 02 — Interceptor Architecture

**Document type:** Component specification
**Audience:** Engineers implementing or integrating with the interceptor layer
**Prerequisites:** `01_overview.md`
**Reading time:** 25 minutes

---

## 1. Why the interceptor is not a library

The single most important architectural decision in Tsukuyomi is that the safety layer is **not a Python library the agent imports**. It is a **network service between the agent and its model provider**. This section explains why, and what that means in practice.

### 1.1 The failure of library-based safety

Consider the alternative: Tsukuyomi as an SDK. The agent author writes `import tsukuyomi` and wraps their LLM calls. This is the pattern used by Guardrails AI, NeMo Guardrails, and LangChain's interruption mechanisms.

This design has three structural problems:

1. **It assumes agent cooperation.** An agent that does not import the library is unprotected. An agent that imports the library can choose not to use it on any specific call. An agent that is modified post-deployment can have the library stripped out. Safety becomes a social contract, not a hard property.

2. **It is agent-specific.** Claude Code users get one story. Cursor users get another. LangChain users get a third. Hermes users get a fourth. A safety property that exists in Claude Code but not in Cursor is not a safety property of AI agents; it is a feature of one vendor's SDK.

3. **It couples safety to implementation.** Every time the agent's SDK updates, there is a risk that the safety hooks break. Claude Code hooks are the canonical example — they exist as a feature, but practitioners report them frequently becoming no-ops across Claude Code version updates, not because Anthropic broke them intentionally but because hook integration is fragile by design.

### 1.2 The interceptor solution

A reverse proxy on the HTTP path between agent and model eliminates all three problems:

1. **No agent cooperation required.** The proxy is in the network path. If the agent wants to reach the model, the request passes through the proxy. If the proxy denies the request, the agent cannot reach the model. Coercion is topological, not social.

2. **Agent-agnostic by construction.** Every modern LLM agent — Claude Code, Hermes, Cursor, Aider, Continue, OpenAI CLI, LangChain, LlamaIndex, AutoGen, custom agents — uses HTTP to talk to its model. They all support configurable base URLs (usually via environment variable). One proxy serves all of them with zero agent-specific code.

3. **Decoupled from agent implementations.** The proxy talks the wire protocol (OpenAI Chat Completions, Anthropic Messages). Wire protocols are stable — they change slowly, with deprecation notices, on published schedules. The proxy does not care how the agent is implemented; it cares only that the agent speaks a known wire format.

### 1.3 The tradeoff we accept

The interceptor design imposes one real cost: **latency**. Every request adds one HTTP hop (agent → Tsukuyomi → upstream → Tsukuyomi → agent). On a fast local deployment this is 1–5ms of overhead for the proxy pass-through, plus whatever time Tsukuyomi spends in the organ pipeline.

For Tier-1 requests, the pipeline overhead is <10ms total (Skin classification, Toe budget check, forward). Negligible relative to the 1–5 second LLM round trip.

For Tier-3 requests, the pipeline overhead can be 5–30 seconds: Protocol Gary makes a separate LLM call, the Shoulders query a GitNexus MCP server, the sandbox executes a plan. This is significant. It is also the *point*: the whole reason the architecture exists is that high-risk operations should not be fast. An agent that deletes the production database in 800ms is fast and dangerous; an agent that takes 30 seconds longer because it was forced to audit, simulate, and verify is slow and correct.

The Skin's tier classification exists specifically so that this overhead is imposed only where it is justified.

## 2. Wire protocol compatibility

### 2.1 Inbound (agent → Tsukuyomi)

Tsukuyomi exposes two HTTP endpoints corresponding to the two dominant wire formats:

**Anthropic Messages API** (used by Claude Code, Cursor in Claude mode, and any Anthropic SDK-based agent):

```
POST /v1/messages
Content-Type: application/json
x-api-key: <agent's key, which Tsukuyomi may verify or rewrite>

{
  "model": "claude-sonnet-4.5",
  "max_tokens": 4096,
  "messages": [ { "role": "user", "content": "..." } ],
  "tools": [ ... ],
  "stream": true
}
```

**OpenAI Chat Completions API** (used by Cursor in OpenAI mode, Hermes with OpenAI provider, LangChain, LlamaIndex, most custom agents):

```
POST /v1/chat/completions
Content-Type: application/json
Authorization: Bearer <agent's key>

{
  "model": "gpt-5.2",
  "messages": [ { "role": "user", "content": "..." } ],
  "tools": [ ... ],
  "stream": true
}
```

On receipt, Tsukuyomi parses both formats into its canonical internal representation (`CanonicalRequest` in `src/tsukuyomi/interceptor/canonical.py`) and the rest of the pipeline operates on this canonical form. Organs do not need to know which wire format the request arrived in.

### 2.2 Outbound (Tsukuyomi → upstream provider)

After the pipeline, the request is serialized in the format expected by the configured upstream:

- Upstream = Anthropic direct → Anthropic Messages format.
- Upstream = OpenAI direct → OpenAI Chat Completions format.
- Upstream = OpenRouter → Tsukuyomi selects format based on OpenRouter's model-specific requirements (most models accept OpenAI format; Anthropic models served through OpenRouter accept either).
- Upstream = Local Ollama → OpenAI Chat Completions format (Ollama's `/api/chat` wire endpoint).
- Upstream = Any OpenAI-compatible endpoint → OpenAI format.
- Upstream = Any Anthropic-compatible endpoint → Anthropic format.

Format conversion between inbound and outbound is handled in `src/tsukuyomi/interceptor/format_adapter.py`. The conversion preserves semantics for all common fields (messages, tools, temperature, max_tokens, streaming, system prompts); where the two APIs differ, documented mappings apply (see `docs/guides/configuration.md` for the table).

### 2.3 Streaming

Both APIs support Server-Sent Events (SSE) streaming. Tsukuyomi preserves streaming end-to-end: the upstream's SSE stream is forwarded chunk-by-chunk to the agent, with Tsukuyomi inspecting and possibly rewriting chunks in transit. There is no buffer-the-whole-response-then-forward pattern — that would add unacceptable perceived latency and would break the UX of long-running agent sessions.

Tool-call events in the stream are the points at which Tsukuyomi's downstream organs (Eyes, Nose) get activated; the stream is paused only when such intervention is required (e.g., Shoulders computing blast radius on a just-emitted tool call).

## 3. Request canonicalization

The canonical internal representation is designed to be a superset of the features both APIs expose. Key fields:

```python
@dataclass
class CanonicalRequest:
    # Origin metadata
    request_id: str                      # Tsukuyomi-assigned UUID
    inbound_format: Literal["anthropic", "openai"]
    agent_hint: Optional[str]            # user-agent header if present
    
    # Core content
    model_requested: str                 # what the agent asked for
    messages: List[Message]              # normalized to a common schema
    system_prompt: Optional[str]
    tools: List[ToolDefinition]
    
    # Parameters
    max_tokens: int
    temperature: float
    stream: bool
    
    # Authorization
    credential: Credential               # rewritten or passed through
    
    # Pipeline state (filled in by organs)
    tier: Optional[Tier] = None
    blast_radius: Optional[BlastRadius] = None
    gary_verdict: Optional[GaryVerdict] = None
    sandbox_result: Optional[SandboxResult] = None
    toe_zone: Optional[BudgetZone] = None
```

This type is the contract between the interceptor layer and the organ layer. Organs read and write fields on this object; the order of reads and writes is determined by the pipeline configuration (Section 4).

## 4. The pipeline

The pipeline is a sequence of organs and protocols applied to a `CanonicalRequest`. The sequence is configured (not hardcoded) so that deployment profiles can choose which organs are active.

The default pipeline for v1.0:

```yaml
# config/pipeline_default.yaml
pipeline:
  - name: skin
    always: true                      # classifies every request
  - name: ears
    when: "request.tier >= 2"
  - name: shoulders
    when: "request.tier == 3 and request.is_code_modifying"
  - name: protocol_gary
    when: "request.tier == 3 or request.blast_radius.risk in ['HIGH', 'CRITICAL']"
  - name: sandbox
    when: "request.tier == 3 and request.has_file_writes"
  - name: knee
    always: true                      # last reflex check before forward
  - name: toe
    always: true                      # last resource check before forward
  - name: forward
    always: true
  - name: eyes
    when: "response.has_tool_calls"
    phase: post
  - name: nose
    always: true
    phase: post
  - name: memory_write
    always: true
    phase: post
```

Tier-1 requests execute steps 1 (skin), 7 (knee), 8 (toe), 9 (forward), 11 (nose), 12 (memory). Everything else is skipped. This is fast.

Tier-3 code-modifying requests execute every step. This is slower. The difference is the point.

## 5. Security properties the interceptor layer guarantees

These are invariants of the interceptor layer itself, independent of which organs are configured:

### 5.1 No direct agent → provider path

No configuration of Tsukuyomi permits the agent to reach the upstream provider directly while Tsukuyomi is running. The only way to bypass Tsukuyomi is to reconfigure the agent to point at a different base URL — which is a human action outside the security model, not an agent capability.

### 5.2 Credential isolation

The agent's API credentials (the `Authorization` header or `x-api-key`) are captured by the interceptor. Tsukuyomi never exposes these credentials back to the agent in any response. The agent-side credential is used by Tsukuyomi to authorize the agent against Tsukuyomi; the upstream-side credential is a separate configuration value, held by Tsukuyomi, never sent back.

This means: even if the agent contains a prompt-injection payload that attempts to exfiltrate its API key, it cannot — because the agent's provider-key, if it has one, was rewritten by Tsukuyomi on ingestion and replaced with a placeholder in any response the agent sees.

### 5.3 No state leakage between requests

Each `CanonicalRequest` has its own state object. Organs may read and write to this object freely; they may not read or write to state from previous requests except through the anatomic memory (which is versioned and audited). There is no global mutable state shared across requests.

### 5.4 Upstream failure isolation

If the upstream provider is unreachable, slow, or returns errors, Tsukuyomi translates these into meaningful errors for the agent (preserving the wire format's error conventions) and records them in the anatomic memory. The Toe treats upstream-provider error-rate as a signal that may trigger AMBER zone; the Nose treats sustained error-rate as an anomaly.

Tsukuyomi does not implement cross-provider fallback in v1.0 (if Anthropic is down, it does not silently route to OpenAI). This is a deliberate conservative choice: automated fallback between providers has subtle correctness implications (prompt templates, tool formats, pricing) that warrant explicit user intent rather than implicit provider-swap.

## 6. Deployment modes

### 6.1 Foreground process (development default)

```bash
tsukuyomi start --port 9999
```

Tsukuyomi logs to stdout; a Ctrl+C shuts it down; the agent loses its model access. This is deliberate; Tsukuyomi should be as much a first-class part of the dev setup as the agent itself.

### 6.2 Systemd service (single-user local production)

```bash
sudo cp scripts/tsukuyomi.service /etc/systemd/system/
sudo systemctl enable tsukuyomi
sudo systemctl start tsukuyomi
```

Tsukuyomi runs as a local service, logs to journald and to `~/.local/share/tsukuyomi/logs/`. The TUI dashboard attaches to the running service.

### 6.3 Container (CI, testing, isolated workloads)

A `Dockerfile` is provided. For CI pipelines that need an interceptor for test runs:

```bash
docker run -d --name tsukuyomi -p 9999:9999 \
  -v $(pwd)/config:/config \
  -v $(pwd)/data:/data \
  tsukuyomi/tsukuyomi:1.0
```

### 6.4 Multi-user / remote (deferred to v2.0)

Not a v1.0 feature. Documented in the research agenda as an area where empirical work is needed before deployment.

## 7. How to verify interception is working

After configuring an agent to point at Tsukuyomi, you can verify interception is active:

```bash
# 1. Check the TUI dashboard — you should see traffic
tsukuyomi dashboard

# 2. Check the logs
tail -f ~/.local/share/tsukuyomi/logs/anatomy.jsonl | jq .

# 3. Send a test request to verify the chain
curl -s http://localhost:9999/v1/messages \
  -H "Content-Type: application/json" \
  -H "x-api-key: $TSUKUYOMI_TEST_KEY" \
  -d '{"model":"claude-haiku-4.6","max_tokens":50,"messages":[{"role":"user","content":"say hi"}]}' \
  | jq .
```

If the agent's request is not appearing in Tsukuyomi logs while the agent is running, interception is not active; see `docs/guides/troubleshooting.md` section *interception not working*.

## 8. What the interceptor does not do

Deliberate exclusions, so the scope is clear:

- **It does not modify model weights.** Tsukuyomi is deployment-layer, not training-layer.
- **It does not detect prompt injection attacks by semantic understanding.** Prompt-injection is a real risk; mitigation is in the Ears (ambiguity detection) and sanitizer utilities, not in the interceptor itself.
- **It does not replace alignment.** A well-aligned model behind Tsukuyomi is safer than either alone. A badly-aligned model behind Tsukuyomi is still a badly-aligned model; Tsukuyomi prevents some classes of damage but cannot make the model itself reliable.
- **It does not cache responses.** Caching is a separate concern (handled by LiteLLM, Portkey, or application-level caching if needed).
- **It does not retry failed requests.** Retries are the agent's responsibility. Tsukuyomi reports the failure honestly.

---

*Next: `03_organs.md` — specifications for each of the eight organs.*
