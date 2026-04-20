# ADR 0005: Tsukuyomi Speaks OpenAI and Anthropic Wire Formats Only (v1.0)

| Field | Value |
| --- | --- |
| **Status** | Accepted (v1.0) |
| **Date** | 2026-04-19 |
| **Decision-makers** | Rob de Vet |

## Context

Tsukuyomi is a reverse-proxy interceptor (ADR 0001). For the proxy to be agent-agnostic, it must accept the wire formats agents already speak. The choice is which formats to support natively.

Major formats in 2026:

- **OpenAI Chat Completions** (`POST /v1/chat/completions`) — universal de facto standard; spoken by OpenAI, Azure OpenAI, OpenRouter, Together AI, Groq, vLLM, Ollama, llama.cpp server, and dozens more.
- **Anthropic Messages** (`POST /v1/messages`) — Anthropic's native API; spoken by Anthropic direct, Bedrock-routed Anthropic models, Vertex AI Anthropic models. Used natively by Claude Code.
- **Google Vertex / Gemini** (`POST /v1/models/.../generateContent`) — Google's native format; less universally adopted by agent frameworks.
- **AWS Bedrock InvokeModel** — AWS-specific; usually accessed through a different SDK.
- **Cohere Chat** — Cohere-specific; small share.

## Decision

**v1.0 supports OpenAI Chat Completions and Anthropic Messages natively, on the inbound side.** On the outbound side, Tsukuyomi can forward to any OpenAI- or Anthropic-compatible endpoint (which includes nearly every backend an agent might use).

Native support for Vertex / Bedrock / Cohere is not in v1.0. Users of those providers can route through OpenRouter or LiteLLM as a translator, with Tsukuyomi sitting in front of the translator.

## Rationale

The OpenAI and Anthropic formats together cover ~95% of agent frameworks observed in the field as of early 2026:

- Claude Code: native Anthropic.
- Cursor: configurable; defaults to OpenAI for OpenAI mode and Anthropic for Claude mode.
- Hermes Agent: OpenAI Chat Completions with optional provider-specific extensions.
- LangChain / LlamaIndex / AutoGen / CrewAI: OpenAI by default, Anthropic via dedicated SDK.
- Bare OpenAI / Anthropic SDKs (used by custom agents): native to each.

Adding Vertex/Bedrock/Cohere natively triples the inbound parsing surface for ~5% of users; the cost-benefit is poor at v1.0. The translator-in-front pattern (LiteLLM, OpenRouter) is operationally trivial and gets these users covered.

## Alternatives considered

### A. OpenAI only

Considered. Rejected because Claude Code (a primary v1.0 target agent) speaks Anthropic natively; forcing Claude Code through a translator introduces format-conversion bugs Tsukuyomi would have to debug indirectly.

### B. OpenAI + Anthropic + Vertex + Bedrock

Considered. Rejected because the parsing/serialization code triples and the testing matrix grows accordingly. Deferred to v1.2.

### C. A new "Tsukuyomi-native" format

Rejected. Inventing a new format would force every agent author to do an integration. The whole point of choosing existing formats is to avoid that.

## Consequences

### Positive

- 95%+ of v1.0-target agents work without translation.
- Wire format is stable (both APIs change slowly with deprecation cycles).
- Format conversion (between inbound OpenAI and outbound Anthropic, or vice versa) is an isolated module.

### Negative

- Vertex/Bedrock/Cohere users need a translator (e.g., LiteLLM in front of Tsukuyomi).
- New providers with novel formats require Tsukuyomi updates to support natively.

## Compliance

PRs adding native support for additional inbound formats are welcome but require: a complete test suite covering streaming and tool-call cases, a corresponding update to format_adapter.py, and an example in `examples/` demonstrating an agent using that format.
