"""Interceptor metrics exposure and request counter behavior."""
from __future__ import annotations

from datetime import datetime, timezone
from types import SimpleNamespace

import httpx
import pytest

from tsukuyomi.core.types import CanonicalRequest, Credential, Decision, Message, Tier
from tsukuyomi.interceptor.server import InterceptorServer
from tsukuyomi.observability import metrics as metrics_module


class _CounterStub:
    def __init__(self) -> None:
        self.calls: list[dict[str, str]] = []

    def labels(self, **kwargs):  # noqa: ANN003
        self.calls.append({k: str(v) for k, v in kwargs.items()})
        return self

    def inc(self) -> None:
        return None


def _server(*, metrics_enabled: bool) -> InterceptorServer:
    cfg = SimpleNamespace(
        host="127.0.0.1",
        port=9999,
        metrics_enabled=metrics_enabled,
        metrics_path="/metrics",
        credential_passthrough=True,
    )
    return InterceptorServer(
        interceptor_config=cfg,
        upstream_config=SimpleNamespace(),
        arbiter=SimpleNamespace(),
    )


@pytest.mark.asyncio
async def test_metrics_endpoint_exposed_when_enabled() -> None:
    server = _server(metrics_enabled=True)
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=server.app),
        base_url="http://testserver",
    ) as client:
        response = await client.get("/metrics")
    assert response.status_code == 200
    assert response.text is not None


@pytest.mark.asyncio
async def test_metrics_endpoint_absent_when_disabled() -> None:
    server = _server(metrics_enabled=False)
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=server.app),
        base_url="http://testserver",
    ) as client:
        response = await client.get("/metrics")
    assert response.status_code == 404


def test_record_request_metric_emits_labels(monkeypatch: pytest.MonkeyPatch) -> None:
    req_counter = _CounterStub()
    organ_counter = _CounterStub()
    monkeypatch.setattr(metrics_module.METRICS, "requests_total", req_counter)
    monkeypatch.setattr(metrics_module.METRICS, "organ_decisions_total", organ_counter)

    req = CanonicalRequest(
        request_id="req_metrics_test",
        inbound_format="openai",
        received_at=datetime.now(timezone.utc),
        model_requested="gpt-4o-mini",
        messages=[Message(role="user", content="hello")],
        system_prompt=None,
        tools=[],
        max_tokens=64,
        temperature=1.0,
        stream=False,
        credential=Credential(raw_header="x", upstream_key="x", rewritten=False),
    )
    req.tier = Tier.ELEVATED
    req.final_decision = Decision.PERMIT

    InterceptorServer._record_request_metric(req, inbound_format="openai")

    assert req_counter.calls == [{"tier": "2", "decision": "permit"}]
    assert organ_counter.calls == [{"organ": "interceptor_openai", "decision": "permit"}]
