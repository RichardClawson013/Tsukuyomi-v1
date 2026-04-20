"""Mouth — human-in-the-loop approval bridge.

Spec: docs/architecture/03_organs.md §4.8.
"""
from __future__ import annotations
import asyncio
import sys
from typing import Any

from tsukuyomi.observability.logging import get_logger

log = get_logger(__name__)


class Mouth:
    def __init__(self, config: Any) -> None:
        self.config = config

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
            # Placeholder. Real webhook implementation is in mouth_webhook.py.
            answer = default
            approved = False
            log.warning("mouth.webhook_not_implemented", default=default)
        else:
            answer = default
            approved = False

        log.info("mouth.decision",
                 interface=interface,
                 triggering_organ=triggering_organ,
                 wait_seconds=0,
                 decision=("approve" if approved else "deny"),
                 default_taken=(answer == default))
        return approved

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
