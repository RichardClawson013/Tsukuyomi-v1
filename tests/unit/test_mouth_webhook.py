"""Webhook approval flow tests for Mouth."""
from __future__ import annotations

import hashlib
import hmac
import json
from typing import Any

import httpx
import pytest

from tsukuyomi.core.config import MouthConfig
from tsukuyomi.organs.mouth import Mouth
from tsukuyomi.organs.mouth_webhook import (
    NONCE_HEADER,
    SIG_HEADER,
    TS_HEADER,
    MouthWebhookClient,
    ReplayGuard,
    sign_payload,
)


def _sign(secret: str, ts: str, nonce: str, body: bytes) -> str:
    msg = f"{ts}.{nonce}.".encode() + body
    return hmac.new(secret.encode(), msg, hashlib.sha256).hexdigest()


class _WebhookTransport(httpx.AsyncBaseTransport):
    def __init__(
        self,
        *,
        secret: str,
        now_ts: int = 1_700_000_000,
        decision: str = "approve",
        approval_id_echo: bool = True,
        signature_mode: str = "valid",
        replay_nonce: str | None = None,
    ) -> None:
        self.secret = secret
        self.now_ts = now_ts
        self.decision = decision
        self.approval_id_echo = approval_id_echo
        self.signature_mode = signature_mode
        self.replay_nonce = replay_nonce

    async def handle_async_request(self, request: httpx.Request) -> httpx.Response:
        req_data = json.loads(request.content.decode())
        approval_id = req_data.get("approval_id", "")
        body_obj: dict[str, Any] = {
            "approval_id": approval_id if self.approval_id_echo else "other",
            "decision": self.decision,
        }
        body = json.dumps(body_obj, separators=(",", ":"), sort_keys=True).encode()
        ts = str(self.now_ts)
        nonce = self.replay_nonce or "resp-nonce-1"
        if self.signature_mode == "invalid":
            sig = "deadbeef"
        else:
            sig = _sign(self.secret, ts, nonce, body)
        headers = {
            TS_HEADER: ts,
            NONCE_HEADER: nonce,
            SIG_HEADER: f"{SIG_PREFIX}{sig}",
            "content-type": "application/json",
        }
        return httpx.Response(status_code=200, headers=headers, content=body, request=request)


@pytest.mark.asyncio
async def test_mouth_webhook_client_approves_valid_signed_response():
    secret = "super-secret"
    transport = _WebhookTransport(secret=secret, decision="approve")
    client = MouthWebhookClient(
        url="https://approval.local/decide",
        secret=secret,
        timeout_seconds=5,
        max_skew_seconds=60,
        replay_window_seconds=60,
        transport=transport,
        now_fn=lambda: 1_700_000_000,
    )

    decision = await client.request_approval({"approval_id": "apr_123"})

    assert decision == "approve"


@pytest.mark.asyncio
async def test_mouth_webhook_client_rejects_invalid_signature():
    secret = "super-secret"
    transport = _WebhookTransport(secret=secret, signature_mode="invalid")
    client = MouthWebhookClient(
        url="https://approval.local/decide",
        secret=secret,
        timeout_seconds=5,
        max_skew_seconds=60,
        replay_window_seconds=60,
        transport=transport,
        now_fn=lambda: 1_700_000_000,
    )

    with pytest.raises(ValueError, match="signature invalid"):
        await client.request_approval({"approval_id": "apr_123"})


@pytest.mark.asyncio
async def test_mouth_webhook_client_rejects_replay_nonce():
    secret = "super-secret"
    transport = _WebhookTransport(secret=secret, replay_nonce="same-nonce")
    client = MouthWebhookClient(
        url="https://approval.local/decide",
        secret=secret,
        timeout_seconds=5,
        max_skew_seconds=60,
        replay_window_seconds=9999,
        transport=transport,
        now_fn=lambda: 1_700_000_000,
    )

    decision = await client.request_approval({"approval_id": "apr_123"})
    assert decision == "approve"
    with pytest.raises(ValueError, match="nonce replay detected"):
        await client.request_approval({"approval_id": "apr_124"})


@pytest.mark.asyncio
async def test_mouth_webhook_client_rejects_timestamp_skew():
    secret = "super-secret"
    transport = _WebhookTransport(secret=secret, now_ts=1_700_000_000)
    client = MouthWebhookClient(
        url="https://approval.local/decide",
        secret=secret,
        timeout_seconds=5,
        max_skew_seconds=5,
        replay_window_seconds=60,
        transport=transport,
        now_fn=lambda: 1_700_001_000,
    )

    with pytest.raises(ValueError, match="outside allowed skew"):
        await client.request_approval({"approval_id": "apr_123"})


@pytest.mark.asyncio
async def test_mouth_webhook_client_rejects_approval_id_mismatch():
    secret = "super-secret"
    transport = _WebhookTransport(secret=secret, approval_id_echo=False)
    client = MouthWebhookClient(
        url="https://approval.local/decide",
        secret=secret,
        timeout_seconds=5,
        max_skew_seconds=60,
        replay_window_seconds=60,
        transport=transport,
        now_fn=lambda: 1_700_000_000,
    )

    with pytest.raises(ValueError, match="approval_id mismatch"):
        await client.request_approval({"approval_id": "apr_123"})


def test_sign_payload_stable():
    secret = "abc"
    ts = "1700000000"
    nonce = "n1"
    body = b'{"approval_id":"apr_1","decision":"approve"}'
    assert sign_payload(secret, ts, nonce, body) == _sign(secret, ts, nonce, body)


def test_replay_guard_ttl():
    now = 10.0
    guard = ReplayGuard(window_seconds=5, now_fn=lambda: now)
    assert guard.consume("n") is True
    assert guard.consume("n") is False


@pytest.mark.asyncio
async def test_mouth_webhook_mode_defaults_to_deny_on_failure(monkeypatch):
    cfg = MouthConfig(
        interface="webhook",
        webhook_url="https://approval.local/decide",
        timeout_seconds=5,
        default_on_timeout="deny",
    )
    monkeypatch.setenv("TSUKUYOMI_MOUTH_WEBHOOK_SECRET", "super-secret")
    mouth = Mouth(cfg)

    class _BrokenClient:
        async def request_approval(self, payload):
            del payload
            raise RuntimeError("network down")

    mouth._webhook_client = _BrokenClient()  # type: ignore[assignment]
    approved = await mouth.request_approval(
        title="Protocol Gary escalation",
        details="Two audit rounds failed",
        proposed_action="drop table users",
        triggering_organ="gary",
    )
    assert approved is False

