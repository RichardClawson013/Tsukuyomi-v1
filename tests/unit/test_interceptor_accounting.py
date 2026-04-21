"""Usage accounting extraction + Toe recording behavior."""
from __future__ import annotations

from datetime import datetime, timezone
from types import SimpleNamespace

import httpx
import pytest

from tsukuyomi.core.types import CanonicalRequest, Credential, Message
from tsukuyomi.interceptor.server import InterceptorServer


class _StubToe:
    def __init__(self) -> None:
        self.calls: list[tuple[str, int, int]] = []

    def record_actual(self, model: str, tokens_in: int, tokens_out: int) -> float:
        self.calls.append((model, tokens_in, tokens_out))
        return 0.12345


class _StubMemory:
    def __init__(self) -> None:
        self.writes = 0

    async def write_request(self, req: CanonicalRequest) -> None:
        del req
        self.writes += 1
        return None


def _server() -> InterceptorServer:
    arbiter = SimpleNamespace(toe=_StubToe(), memory=_StubMemory())
    return InterceptorServer(
        interceptor_config=SimpleNamespace(host="127.0.0.1", port=9999),
        upstream_config=SimpleNamespace(),
        arbiter=arbiter,  # type: ignore[arg-type]
    )


def _req(model_requested: str = "gpt-4o-mini", model_used: str | None = None) -> CanonicalRequest:
    return CanonicalRequest(
        request_id="req_usage_test",
        inbound_format="openai",
        received_at=datetime.now(timezone.utc),
        model_requested=model_requested,
        messages=[Message(role="user", content="hello")],
        system_prompt=None,
        tools=[],
        max_tokens=128,
        temperature=1.0,
        stream=False,
        credential=Credential(raw_header="x", upstream_key="x", rewritten=False),
        model_used=model_used,
    )


def _resp(body: dict, status_code: int = 200) -> httpx.Response:
    req = httpx.Request("POST", "https://upstream.example/v1/chat/completions")
    return httpx.Response(status_code=status_code, json=body, request=req)


def test_extract_usage_tokens_openai_shape() -> None:
    payload = {"usage": {"prompt_tokens": 12, "completion_tokens": 34}}
    got = InterceptorServer._extract_usage_tokens(payload, wire_format="openai")
    assert got == (12, 34)


def test_extract_usage_tokens_anthropic_shape() -> None:
    payload = {"usage": {"input_tokens": 7, "output_tokens": 9}}
    got = InterceptorServer._extract_usage_tokens(payload, wire_format="anthropic")
    assert got == (7, 9)


def test_extract_usage_tokens_returns_none_when_missing() -> None:
    payload = {"id": "x"}
    got = InterceptorServer._extract_usage_tokens(payload, wire_format="openai")
    assert got == (None, None)


@pytest.mark.asyncio
async def test_record_usage_openai_updates_request_and_calls_toe() -> None:
    server = _server()
    req = _req(model_requested="gpt-4o-mini", model_used="gpt-4o-mini")
    response = _resp({"usage": {"prompt_tokens": 100, "completion_tokens": 50}})

    server._record_usage(req, response, provider="openai", wire_format="openai")
    if server._last_write_task is not None:
        await server._last_write_task

    assert req.tokens_in == 100
    assert req.tokens_out == 50
    assert req.cost_usd == pytest.approx(0.12345)
    assert server.arbiter.toe.calls == [("gpt-4o-mini", 100, 50)]
    assert server.arbiter.memory.writes == 1


@pytest.mark.asyncio
async def test_record_usage_anthropic_uses_model_requested_when_no_model_used() -> None:
    server = _server()
    req = _req(model_requested="claude-sonnet-4.5", model_used=None)
    response = _resp({"usage": {"input_tokens": 200, "output_tokens": 20}})

    server._record_usage(req, response, provider="anthropic", wire_format="anthropic")
    if server._last_write_task is not None:
        await server._last_write_task

    assert req.tokens_in == 200
    assert req.tokens_out == 20
    assert server.arbiter.toe.calls == [("claude-sonnet-4.5", 200, 20)]


def test_record_usage_ignores_error_status() -> None:
    server = _server()
    req = _req()
    response = _resp({"usage": {"prompt_tokens": 100, "completion_tokens": 50}}, status_code=500)

    server._record_usage(req, response, provider="openai", wire_format="openai")

    assert req.tokens_in is None
    assert server.arbiter.toe.calls == []
