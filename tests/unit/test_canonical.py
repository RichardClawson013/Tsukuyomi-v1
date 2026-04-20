"""Wire-format ↔ canonical conversion."""
from tsukuyomi.interceptor.canonical import (
    anthropic_to_canonical, openai_to_canonical,
    canonical_to_anthropic, canonical_to_openai,
)


def test_anthropic_roundtrip():
    body = {
        "model": "claude-sonnet-4.5",
        "max_tokens": 100,
        "messages": [{"role": "user", "content": "hi"}],
    }
    c = anthropic_to_canonical(body, "x-key", "up-key")
    assert c.inbound_format == "anthropic"
    assert c.model_requested == "claude-sonnet-4.5"
    assert c.messages[0].content == "hi"
    out = canonical_to_anthropic(c)
    assert out["model"] == "claude-sonnet-4.5"
    assert out["messages"][0]["content"] == "hi"


def test_openai_roundtrip():
    body = {
        "model": "gpt-5.2",
        "messages": [
            {"role": "system", "content": "be helpful"},
            {"role": "user", "content": "hi"},
        ],
    }
    c = openai_to_canonical(body, "Bearer k", "up-key")
    assert c.system_prompt == "be helpful"
    out = canonical_to_openai(c)
    assert out["messages"][0]["role"] == "system"


def test_openai_tools():
    body = {
        "model": "gpt-5.2",
        "messages": [{"role": "user", "content": "x"}],
        "tools": [{"type": "function", "function": {
            "name": "read_file", "description": "reads a file",
            "parameters": {"type": "object", "properties": {"path": {"type": "string"}}}
        }}]
    }
    c = openai_to_canonical(body, "", "")
    assert len(c.tools) == 1
    assert c.tools[0].name == "read_file"
