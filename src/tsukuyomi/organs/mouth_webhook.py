"""Webhook client for Mouth approvals with HMAC verification."""
from __future__ import annotations

import hashlib
import hmac
import json
import time
import uuid
from typing import Any, Callable

import httpx

TS_HEADER = "X-Tsukuyomi-Timestamp"
NONCE_HEADER = "X-Tsukuyomi-Nonce"
SIG_HEADER = "X-Tsukuyomi-Signature"
SIG_PREFIX = "v1="
ALLOWED_DECISIONS = {"approve", "deny", "abort_all"}


def sign_payload(secret: str, timestamp: str, nonce: str, body: bytes) -> str:
    message = f"{timestamp}.{nonce}.".encode() + body
    return hmac.new(secret.encode(), message, hashlib.sha256).hexdigest()


def verify_payload_signature(secret: str, timestamp: str, nonce: str,
                             body: bytes, signature_header: str) -> bool:
    if not signature_header:
        return False
    got = signature_header.strip()
    if got.startswith(SIG_PREFIX):
        got = got[len(SIG_PREFIX):]
    expected = sign_payload(secret, timestamp, nonce, body)
    return hmac.compare_digest(got, expected)


class ReplayGuard:
    """In-memory nonce replay prevention with TTL."""

    def __init__(self, window_seconds: int, now_fn: Callable[[], float] | None = None) -> None:
        self.window_seconds = max(int(window_seconds), 1)
        self._now = now_fn or time.time
        self._seen: dict[str, float] = {}

    def consume(self, nonce: str) -> bool:
        now = float(self._now())
        self._purge(now)
        exp = self._seen.get(nonce)
        if exp is not None and exp >= now:
            return False
        self._seen[nonce] = now + self.window_seconds
        return True

    def _purge(self, now: float) -> None:
        for key, exp in list(self._seen.items()):
            if exp < now:
                del self._seen[key]


class MouthWebhookClient:
    def __init__(
        self,
        *,
        url: str,
        secret: str,
        timeout_seconds: int,
        max_skew_seconds: int,
        replay_window_seconds: int,
        transport: httpx.AsyncBaseTransport | None = None,
        now_fn: Callable[[], float] | None = None,
    ) -> None:
        self.url = url
        self.secret = secret
        self.timeout_seconds = int(timeout_seconds)
        self.max_skew_seconds = int(max_skew_seconds)
        self._transport = transport
        self._now = now_fn or time.time
        self._replay = ReplayGuard(replay_window_seconds, now_fn=self._now)

    async def request_approval(self, payload: dict[str, Any]) -> str:
        req_body = json.dumps(payload, separators=(",", ":"), sort_keys=True).encode()
        req_ts = str(int(self._now()))
        req_nonce = uuid.uuid4().hex
        req_sig = sign_payload(self.secret, req_ts, req_nonce, req_body)
        headers = {
            "content-type": "application/json",
            TS_HEADER: req_ts,
            NONCE_HEADER: req_nonce,
            SIG_HEADER: f"{SIG_PREFIX}{req_sig}",
        }

        async with httpx.AsyncClient(
            timeout=float(self.timeout_seconds),
            transport=self._transport,
        ) as client:
            response = await client.post(self.url, content=req_body, headers=headers)
            response.raise_for_status()
        return self._parse_verified_response(response, expected_approval_id=str(payload["approval_id"]))

    def _parse_verified_response(self, response: httpx.Response, *,
                                 expected_approval_id: str) -> str:
        ts = response.headers.get(TS_HEADER, "")
        nonce = response.headers.get(NONCE_HEADER, "")
        signature = response.headers.get(SIG_HEADER, "")
        if not ts or not nonce or not signature:
            raise ValueError("Webhook response missing signature headers")

        try:
            ts_int = int(ts)
        except ValueError as exc:
            raise ValueError("Webhook response timestamp invalid") from exc
        now = int(self._now())
        if abs(now - ts_int) > self.max_skew_seconds:
            raise ValueError("Webhook response timestamp outside allowed skew")
        if not self._replay.consume(nonce):
            raise ValueError("Webhook response nonce replay detected")
        if not verify_payload_signature(self.secret, ts, nonce, response.content, signature):
            raise ValueError("Webhook response signature invalid")

        data = response.json()
        if not isinstance(data, dict):
            raise ValueError("Webhook response JSON must be an object")
        if str(data.get("approval_id", "")) != expected_approval_id:
            raise ValueError("Webhook response approval_id mismatch")
        decision = str(data.get("decision", "")).strip().lower()
        if decision not in ALLOWED_DECISIONS:
            raise ValueError(f"Webhook response decision invalid: {decision}")
        return decision
