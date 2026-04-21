"""Mouth — human-in-the-loop approval bridge.

Spec: docs/architecture/03_organs.md §4.8.
"""
from __future__ import annotations
import asyncio
import os
import sys
import uuid
from typing import Any

from tsukuyomi.organs.mouth_webhook import MouthWebhookClient
from tsukuyomi.observability.logging import get_logger

log = get_logger(__name__)


class Mouth:
    def __init__(self, config: Any) -> None:
        self.config = config
        self._webhook_client: MouthWebhookClient | None = None

    async def request_approval(self, *, title: str, details: str,
                               proposed_action: str,
                               triggering_organ: str) -> bool:
        """Block until the human responds (or timeout → default_on_timeout)."""
        interface = getattr(self.config, "interface", "cli")
        timeout = int(getattr(self.config, "timeout_seconds", 120))
        default = getattr(self.config, "default_on_timeout", "deny")

        if interface == "cli":
            answer = await self._cli_prompt(title, details, proposed_action,
                                             triggering_organ, timeout)
            approved = (answer or default) == "approve"
        elif interface == "webhook":
            answer = await self._webhook_prompt(
                title=title,
                details=details,
                proposed_action=proposed_action,
                triggering_organ=triggering_organ,
                timeout_s=timeout,
                default=default,
            )
            approved = (answer or default) == "approve"
        else:
            answer = default
            approved = False

        log.info("mouth.decision",
                 interface=interface,
                 triggering_organ=triggering_organ,
                 wait_seconds=timeout,
                 decision=("approve" if approved else "deny"),
                 default_taken=(answer == default))
        return approved

    async def _webhook_prompt(self, *, title: str, details: str,
                              proposed_action: str, triggering_organ: str,
                              timeout_s: int, default: str) -> str:
        client = self._get_or_create_webhook_client(timeout_s=timeout_s)
        if client is None:
            log.warning("mouth.webhook_unconfigured", default=default)
            return default
        payload = {
            "approval_id": f"apr_{uuid.uuid4().hex[:12]}",
            "title": title,
            "details": details,
            "proposed_action": proposed_action[:240],
            "triggering_organ": triggering_organ,
            "default": default,
            "timeout_seconds": timeout_s,
        }
        try:
            return await client.request_approval(payload)
        except Exception as exc:  # noqa: BLE001
            log.warning("mouth.webhook_failed", error=str(exc), default=default)
            return default

    def _get_or_create_webhook_client(self, *, timeout_s: int) -> MouthWebhookClient | None:
        if self._webhook_client is not None:
            return self._webhook_client
        url = getattr(self.config, "webhook_url", None)
        secret_env = getattr(self.config, "webhook_secret_env_var", "TSUKUYOMI_MOUTH_WEBHOOK_SECRET")
        secret = os.environ.get(secret_env, "")
        if not url or not secret:
            return None
        max_skew = int(getattr(self.config, "webhook_max_skew_seconds", 300))
        replay_window = int(getattr(self.config, "webhook_replay_window_seconds", 600))
        self._webhook_client = MouthWebhookClient(
            url=str(url),
            secret=secret,
            timeout_seconds=timeout_s,
            max_skew_seconds=max_skew,
            replay_window_seconds=replay_window,
        )
        return self._webhook_client

    @staticmethod
    async def _cli_prompt(title: str, details: str, proposed_action: str,
                          triggering_organ: str, timeout_s: int) -> str | None:
        print("\n" + "=" * 72, file=sys.stderr)
        print(f"🔔 MOUTH APPROVAL REQUIRED — {title}", file=sys.stderr)
        print(f"   Triggered by: {triggering_organ}", file=sys.stderr)
        print(f"   Details     : {details}", file=sys.stderr)
        print(f"   Action      : {proposed_action[:240]}", file=sys.stderr)
        print(f"   Respond     : [a]pprove / [d]eny / [q]uit   (timeout {timeout_s}s → deny)",
              file=sys.stderr)
        print("=" * 72, file=sys.stderr)

        loop = asyncio.get_running_loop()
        try:
            answer = await asyncio.wait_for(
                loop.run_in_executor(None, sys.stdin.readline),
                timeout=timeout_s,
            )
        except asyncio.TimeoutError:
            return None
        ans = (answer or "").strip().lower()
        if ans.startswith("a"):
            return "approve"
        if ans.startswith("q"):
            return "abort_all"
        return "deny"
