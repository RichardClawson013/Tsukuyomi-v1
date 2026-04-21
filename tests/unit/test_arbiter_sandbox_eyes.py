"""Arbiter behavior around sandbox mismatch and Eyes verification."""
from __future__ import annotations

from types import SimpleNamespace

import pytest

from tsukuyomi.core.arbiter import Arbiter
from tsukuyomi.core.config import Config
from tsukuyomi.core.types import (
    BlastRisk,
    BlastRadius,
    CanonicalRequest,
    Credential,
    Decision,
    Message,
    SandboxResult,
    Tier,
)


class _NoopMemory:
    async def write_request(self, req):
        del req


class _NoopSkin:
    async def classify(self, req):
        req.tier = req.tier or Tier.HIGH_RISK


class _NoopEars:
    async def evaluate(self, req):
        del req
        return SimpleNamespace(clear=True, reasons=[])


class _NoopShoulders:
    async def analyze(self, req):
        if req.blast_radius is None:
            req.blast_radius = BlastRadius(
                target_symbol="x",
                direct_callers=0,
                affected_files=[],
                risk=BlastRisk.LOW,
            )


class _NoopKnee:
    def check(self, req):
        del req
        return SimpleNamespace(permitted=True, matched_pattern_id=None)


class _NoopToe:
    total_today = 0.0

    async def evaluate(self, req):
        del req
        return "GREEN"


class _NoopGary:
    async def audit(self, req):
        del req
        return SimpleNamespace(final_decision="PASS")


class _SandboxStub:
    def __init__(self, result: SandboxResult) -> None:
        self._result = result

    async def simulate(self, req):
        req.sandbox_result = self._result
        return self._result


class _EyesStub:
    def __init__(self, *, match: bool, mismatches: int) -> None:
        self._result = SimpleNamespace(
            match=match,
            surprise_files=["surprise.py"] if not match else [],
            missing_files=["expected.py"] if not match else [],
        )
        self._session_mismatches = mismatches

    async def verify_expected_vs_actual(self, expected_files, actual_files):
        del expected_files, actual_files
        return self._result

    @property
    def session_mismatches(self) -> int:
        return self._session_mismatches


class _MouthStub:
    def __init__(self, answers: list[bool]) -> None:
        self.answers = answers
        self.calls: list[dict[str, str]] = []

    async def request_approval(self, *, title, details, proposed_action, triggering_organ):
        self.calls.append({
            "title": title,
            "details": details,
            "proposed_action": proposed_action,
            "triggering_organ": triggering_organ,
        })
        if self.answers:
            return self.answers.pop(0)
        return False


def _req() -> CanonicalRequest:
    req = CanonicalRequest(
        request_id="req_arbiter_sandbox_eyes",
        inbound_format="openai",
        received_at=CanonicalRequest.now(),
        model_requested="gpt-4o-mini",
        messages=[Message(role="user", content="please apply this plan")],
        system_prompt=None,
        tools=[],
        max_tokens=128,
        temperature=1.0,
        stream=False,
        credential=Credential(raw_header="x", upstream_key="x", rewritten=False),
    )
    req.tier = Tier.HIGH_RISK
    req.has_file_writes = True
    req.is_code_modifying = True
    req.blast_radius = BlastRadius(target_symbol="safe", direct_callers=0, affected_files=[], risk=BlastRisk.LOW)
    return req


def _arbiter(*, sandbox_result: SandboxResult, eyes_match: bool, eyes_mismatches: int,
             mouth_answers: list[bool]) -> tuple[Arbiter, _MouthStub]:
    cfg = Config()
    cfg.protocols.gary.enabled = False
    cfg.organs.eyes.block_on_repeated_mismatch = True
    cfg.organs.eyes.mismatch_threshold_per_session = 3
    mouth = _MouthStub(mouth_answers)

    return Arbiter(
        config=cfg,
        nerve=SimpleNamespace(),
        memory=_NoopMemory(),
        skin=_NoopSkin(),
        ears=_NoopEars(),
        shoulders=_NoopShoulders(),
        knee=_NoopKnee(),
        toe=_NoopToe(),
        eyes=_EyesStub(match=eyes_match, mismatches=eyes_mismatches),
        nose=SimpleNamespace(),
        mouth=mouth,
        sandbox=_SandboxStub(sandbox_result),
        gary=_NoopGary(),
    ), mouth


@pytest.mark.asyncio
async def test_sandbox_mismatch_denied_blocks() -> None:
    result = SandboxResult(
        sandbox_id="s1",
        plan_summary="plan",
        expected_files=["a.py"],
        actual_files=["b.py"],
        match_score=0.0,
        passed=False,
        cleanup_status="clean",
    )
    arbiter, mouth = _arbiter(
        sandbox_result=result,
        eyes_match=True,
        eyes_mismatches=0,
        mouth_answers=[False],
    )
    req = _req()

    out = await arbiter.process(req)
    assert out.final_decision == Decision.BLOCK
    assert out.block_reason == "sandbox_mismatch_denied"
    assert mouth.calls[0]["triggering_organ"] == "sandbox"


@pytest.mark.asyncio
async def test_eyes_mismatch_denied_blocks() -> None:
    result = SandboxResult(
        sandbox_id="s1",
        plan_summary="plan",
        expected_files=["a.py"],
        actual_files=["a.py"],
        match_score=1.0,
        passed=True,
        cleanup_status="clean",
    )
    arbiter, mouth = _arbiter(
        sandbox_result=result,
        eyes_match=False,
        eyes_mismatches=1,
        mouth_answers=[False],
    )
    req = _req()

    out = await arbiter.process(req)
    assert out.final_decision == Decision.BLOCK
    assert out.block_reason == "eyes_mismatch_denied"
    assert mouth.calls[0]["triggering_organ"] == "eyes"


@pytest.mark.asyncio
async def test_eyes_repeated_mismatch_threshold_blocks_even_if_approved() -> None:
    result = SandboxResult(
        sandbox_id="s1",
        plan_summary="plan",
        expected_files=["a.py"],
        actual_files=["a.py"],
        match_score=1.0,
        passed=True,
        cleanup_status="clean",
    )
    arbiter, mouth = _arbiter(
        sandbox_result=result,
        eyes_match=False,
        eyes_mismatches=3,
        mouth_answers=[True],
    )
    req = _req()

    out = await arbiter.process(req)
    assert out.final_decision == Decision.BLOCK
    assert out.block_reason == "eyes_repeated_mismatch_threshold"
    assert mouth.calls[0]["triggering_organ"] == "eyes"
