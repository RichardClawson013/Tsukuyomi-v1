"""Conversion between OpenAI/Anthropic wire format and CanonicalRequest."""
from __future__ import annotations
import uuid
from datetime import datetime, timezone
from typing import Any, Literal

from tsukuyomi.core.types import (
    CanonicalRequest, Credential, Message, ToolDefinition,
)


def anthropic_to_canonical(body: dict[str, Any], raw_auth_header: str,
                           upstream_key: str, agent_hint: str | None = None) -> CanonicalRequest:
    messages = []
    for m in body.get("messages", []):
        content = m.get("content", "")
        if isinstance(content, list):
            # Anthropic allows content blocks; join text blocks
            content = "\n".join(
                b.get("text", "") for b in content if b.get("type") == "text"
            )
        messages.append(Message(role=m["role"], content=content or ""))

    tools = [
        ToolDefinition(
            name=t["name"],
            description=t.get("description", ""),
            parameters_schema=t.get("input_schema", {}),
        )
        for t in body.get("tools", [])
    ]

    return CanonicalRequest(
        request_id=f"req_{uuid.uuid4().hex[:10]}",
        inbound_format="anthropic",
        received_at=datetime.now(timezone.utc),
        model_requested=body.get("model", ""),
        messages=messages,
        system_prompt=body.get("system"),
        tools=tools,
        max_tokens=int(body.get("max_tokens", 4096)),
        temperature=float(body.get("temperature", 1.0)),
        stream=bool(body.get("stream", False)),
        credential=Credential(raw_header=raw_auth_header,
                              upstream_key=upstream_key,
                              rewritten=(raw_auth_header != upstream_key)),
        agent_hint=agent_hint,
    )


def openai_to_canonical(body: dict[str, Any], raw_auth_header: str,
                        upstream_key: str, agent_hint: str | None = None) -> CanonicalRequest:
    messages = []
    system_prompt = None
    for m in body.get("messages", []):
        role = m.get("role", "user")
        if role == "system":
            system_prompt = m.get("content", "")
            continue
        messages.append(Message(role=role, content=m.get("content", "") or "",
                                name=m.get("name"),
                                tool_calls=m.get("tool_calls", []),
                                tool_call_id=m.get("tool_call_id")))

    tools = []
    for t in body.get("tools", []):
        if t.get("type") == "function":
            f = t.get("function", {})
            tools.append(ToolDefinition(
                name=f.get("name", ""),
                description=f.get("description", ""),
                parameters_schema=f.get("parameters", {}),
            ))

    return CanonicalRequest(
        request_id=f"req_{uuid.uuid4().hex[:10]}",
        inbound_format="openai",
        received_at=datetime.now(timezone.utc),
        model_requested=body.get("model", ""),
        messages=messages,
        system_prompt=system_prompt,
        tools=tools,
        max_tokens=int(body.get("max_tokens", body.get("max_completion_tokens", 4096))),
        temperature=float(body.get("temperature", 1.0)),
        stream=bool(body.get("stream", False)),
        credential=Credential(raw_header=raw_auth_header,
                              upstream_key=upstream_key,
                              rewritten=(raw_auth_header != upstream_key)),
        agent_hint=agent_hint,
    )


def canonical_to_anthropic(req: CanonicalRequest) -> dict[str, Any]:
    msgs = [{"role": m.role, "content": m.content} for m in req.messages if m.role != "system"]
    body: dict[str, Any] = {
        "model": req.model_used or req.model_requested,
        "max_tokens": req.max_tokens,
        "messages": msgs,
        "stream": req.stream,
    }
    if req.temperature != 1.0:
        body["temperature"] = req.temperature
    if req.system_prompt:
        body["system"] = req.system_prompt
    if req.tools:
        body["tools"] = [
            {"name": t.name, "description": t.description, "input_schema": t.parameters_schema}
            for t in req.tools
        ]
    return body


def canonical_to_openai(req: CanonicalRequest) -> dict[str, Any]:
    msgs: list[dict[str, Any]] = []
    if req.system_prompt:
        msgs.append({"role": "system", "content": req.system_prompt})
    for m in req.messages:
        msgs.append({"role": m.role, "content": m.content})
    body: dict[str, Any] = {
        "model": req.model_used or req.model_requested,
        "messages": msgs,
        "stream": req.stream,
    }
    if req.max_tokens:
        body["max_tokens"] = req.max_tokens
    if req.temperature != 1.0:
        body["temperature"] = req.temperature
    if req.tools:
        body["tools"] = [
            {"type": "function",
             "function": {"name": t.name, "description": t.description,
                          "parameters": t.parameters_schema}}
            for t in req.tools
        ]
    return body
