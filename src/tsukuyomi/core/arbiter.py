"""Arbiter — orchestrates the request pipeline.

Reads the pipeline configuration, sequences the organs and protocols,
publishes signals to NerveCore, and persists results.
"""
from __future__ import annotations
import asyncio
from typing import TYPE_CHECKING

from tsukuyomi.core.types import CanonicalRequest, Decision

if TYPE_CHECKING:
    from tsukuyomi.core.config import Config
    from tsukuyomi.core.nervecore import NerveCoreInterface
    from tsukuyomi.organs import (
        Skin, Ears, Shoulders, Knee, Toe, Eyes, Nose, Mouth,
    )
    from tsukuyomi.organs.sandbox.base import SandboxBackend
    from tsukuyomi.protocols.gary import ProtocolGary
    from tsukuyomi.memory.base import MemoryBackend


class Arbiter:
    """Owns the pipeline. Stateless across requests; threadsafe via asyncio."""

    def __init__(
        self,
        config: "Config",
        nerve: "NerveCoreInterface",
        memory: "MemoryBackend",
        skin: "Skin", ears: "Ears", shoulders: "Shoulders",
        knee: "Knee", toe: "Toe", eyes: "Eyes",
        nose: "Nose", mouth: "Mouth",
        sandbox: "SandboxBackend",
        gary: "ProtocolGary",
    ) -> None:
        self.config = config
        self.nerve = nerve
        self.memory = memory
        self.skin = skin
        self.ears = ears
        self.shoulders = shoulders
        self.knee = knee
        self.toe = toe
        self.eyes = eyes
        self.nose = nose
        self.mouth = mouth
        self.sandbox = sandbox
        self.gary = gary

    async def process(self, req: CanonicalRequest) -> CanonicalRequest:
        """Run the request through the configured pipeline.

        Returns the request with `final_decision` set. The interceptor layer
        consults `final_decision` to determine whether to forward to upstream
        or to return an error to the agent.
        """
        await self.skin.classify(req)

        if req.tier and req.tier.value >= 2 and self.config.organs.ears.enabled:
            verdict = await self.ears.evaluate(req)
            if not verdict.clear:
                approved = await self.mouth.request_approval(
                    title="Ambiguous request",
                    details=f"Reasons: {verdict.reasons}",
                    proposed_action=req.messages[-1].content[:200],
                    triggering_organ="ears",
                )
                if not approved:
                    req.final_decision = Decision.BLOCK
                    req.block_reason = f"ambiguous: {verdict.reasons}"
                    await self.memory.write_request(req)
                    return req

        if req.tier and req.tier.value == 3 and req.is_code_modifying                 and self.config.organs.shoulders.enabled:
            await self.shoulders.analyze(req)

        if self._gary_should_run(req) and self.config.protocols.gary.enabled:
            verdict = await self.gary.audit(req)
            if verdict.final_decision == "BLOCK":
                req.final_decision = Decision.BLOCK
                req.block_reason = "protocol_gary_block"
                await self.memory.write_request(req)
                return req
            if verdict.final_decision == "ESCALATED":
                approved = await self.mouth.request_approval(
                    title="Protocol Gary escalation",
                    details="Two audit rounds failed",
                    proposed_action=req.messages[-1].content[:200],
                    triggering_organ="gary",
                )
                if not approved:
                    req.final_decision = Decision.BLOCK
                    req.block_reason = "gary_escalation_denied"
                    await self.memory.write_request(req)
                    return req

        if req.tier and req.tier.value == 3 and req.has_file_writes:
            await self.sandbox.simulate(req)

        knee_verdict = self.knee.check(req)
        if not knee_verdict.permitted:
            req.final_decision = Decision.BLOCK
            req.block_reason = f"knee:{knee_verdict.matched_pattern_id}"
            await self.memory.write_request(req)
            return req

        toe_decision = await self.toe.evaluate(req)
        if toe_decision == "RED":
            approved = await self.mouth.request_approval(
                title="Budget RED zone",
                details=f"Daily budget exhausted: today=${self.toe.total_today:.4f}",
                proposed_action="Continue with this request?",
                triggering_organ="toe",
            )
            if not approved:
                req.final_decision = Decision.BLOCK
                req.block_reason = "toe_red_denied"
                await self.memory.write_request(req)
                return req

        req.final_decision = Decision.PERMIT
        await self.memory.write_request(req)
        return req

    def _gary_should_run(self, req: CanonicalRequest) -> bool:
        cfg = self.config.protocols.gary
        if req.tier and req.tier.value in cfg.activate_on_tier:
            return True
        if req.blast_radius and req.blast_radius.risk.value in cfg.activate_on_risk:
            return True
        last_user_msg = next((m.content for m in reversed(req.messages) if m.role == "user"), "")
        for kw in cfg.activate_on_irreversible_keywords:
            if kw.lower() in last_user_msg.lower():
                return True
        return False
