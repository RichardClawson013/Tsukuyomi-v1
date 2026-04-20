# Integrating a Custom Agent with Tsukuyomi

**Audience:** Developers building their own agent or using a framework not covered elsewhere.
**Prerequisites:** Tsukuyomi running.

---

## 1. The general principle

If your agent uses the OpenAI or Anthropic Python SDK (or any compatible HTTP client), all you need to do is point its `base_url` at Tsukuyomi.

## 2. OpenAI Python SDK

```python
from openai import OpenAI

client = OpenAI(
    api_key="placeholder-tsukuyomi-rewrites-this",
    base_url="http://localhost:9999/v1"
)

response = client.chat.completions.create(
    model="gpt-4o",
    messages=[{"role": "user", "content": "list the files in /tmp"}]
)
```

## 3. Anthropic Python SDK

```python
from anthropic import Anthropic

client = Anthropic(
    api_key="placeholder",
    base_url="http://localhost:9999"
)

response = client.messages.create(
    model="claude-sonnet-4.5",
    max_tokens=1024,
    messages=[{"role": "user", "content": "list the files in /tmp"}]
)
```

## 4. LangChain

```python
from langchain_openai import ChatOpenAI

llm = ChatOpenAI(
    model="gpt-4o",
    base_url="http://localhost:9999/v1",
    api_key="placeholder"
)
```

For LangChain Anthropic:

```python
from langchain_anthropic import ChatAnthropic

llm = ChatAnthropic(
    model="claude-sonnet-4.5",
    base_url="http://localhost:9999",
    api_key="placeholder"
)
```

## 5. LlamaIndex

```python
from llama_index.llms.openai import OpenAI

llm = OpenAI(
    model="gpt-4o",
    api_base="http://localhost:9999/v1",
    api_key="placeholder"
)
```

## 6. Raw httpx

```python
import httpx

resp = httpx.post(
    "http://localhost:9999/v1/chat/completions",
    json={
        "model": "gpt-4o",
        "messages": [{"role": "user", "content": "hi"}]
    },
    headers={"Authorization": "Bearer placeholder"}
)
```

## 7. Streaming

All wire-format clients support streaming. Tsukuyomi preserves SSE end-to-end:

```python
stream = client.chat.completions.create(
    model="gpt-4o",
    messages=[...],
    stream=True
)
for chunk in stream:
    print(chunk.choices[0].delta.content, end="")
```

## 8. Tool calls

Tool definitions and tool-call responses pass through Tsukuyomi unchanged in shape. The Knee inspects every emitted tool call before it is delivered to your client; if a tool call matches a destructive pattern, Tsukuyomi blocks it and returns an OpenAI-style error or Anthropic-style error_response according to the inbound format.

## 9. What to identify your agent as

Tsukuyomi reads the User-Agent header to derive `agent_hint` for logs and dashboards. Set it for visibility:

```python
client = OpenAI(
    base_url="http://localhost:9999/v1",
    api_key="placeholder",
    default_headers={"User-Agent": "myagent/1.0"}
)
```

## 10. Authentication of *your client* against Tsukuyomi

By default Tsukuyomi accepts any incoming request from `127.0.0.1`. For network-exposed deployments, configure a token-based gate:

```json
"interceptor": {
  "require_client_token": true,
  "client_tokens_env_var": "TSUKUYOMI_CLIENT_TOKENS"  // comma-separated
}
```

Then your client passes the token:

```python
client = OpenAI(
    base_url="http://localhost:9999/v1",
    api_key="my-tsukuyomi-token-here",
    default_headers={"X-Tsukuyomi-Client-Token": "my-tsukuyomi-token-here"}
)
```

This is separate from upstream provider credentials.
