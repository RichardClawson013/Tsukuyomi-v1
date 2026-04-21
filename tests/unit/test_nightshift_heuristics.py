"""NightShift heuristic proposal generation tests."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from tsukuyomi.core.config import Config, MemoryConfig
from tsukuyomi.memory.sqlite_backend import SQLiteMemoryBackend
from tsukuyomi.protocols import nightshift


@pytest.mark.asyncio
async def test_audit_evasion_heuristic_generates_proposal(tmp_path: Path) -> None:
    mem = SQLiteMemoryBackend(MemoryConfig(sqlite_path=str(tmp_path / "memory.db")))
    await mem.initialize()
    since = datetime.now(timezone.utc) - timedelta(hours=24)
    now = datetime.now(timezone.utc).isoformat()

    rounds = [
        {
            "round": 1,
            "approved": False,
            "reasons": ["evasion_phrase:it's fine", "Q1_too_short(3<150)"],
        },
        {"round": 2, "approved": True, "reasons": []},
    ]
    for idx in range(2):
        await mem.write_audit({
            "audit_id": f"aud_{idx}",
            "request_id": f"req_{idx}",
            "ts_utc": now,
            "action_summary": "drop table users",
            "triggering_organ": "gary",
            "rounds": rounds,
            "final_decision": "PASS",
            "mouth_escalation": None,
            "human_override": 0,
            "audit_cost_usd": 0.0,
            "audit_latency_seconds": 0.1,
        })

    props = await nightshift._heuristic_audit_evasion(mem, since, Config())
    await mem.shutdown()

    assert props, "Expected audit evasion proposal"
    assert props[0]["heuristic"] == "audit_evasion_patterns"
    assert "it's fine" in props[0]["observation"]


@pytest.mark.asyncio
async def test_skin_drift_heuristic_detects_tier1_risky_blocks(tmp_path: Path) -> None:
    mem = SQLiteMemoryBackend(MemoryConfig(sqlite_path=str(tmp_path / "memory.db")))
    await mem.initialize()
    since = datetime.now(timezone.utc) - timedelta(hours=24)
    now = datetime.now(timezone.utc)

    for i in range(20):
        req = _make_req(
            request_id=f"req_{i}",
            ts=now,
            tier=1,
            final_decision="block" if i < 3 else "permit",
            block_reason="knee:rm_slash_root" if i < 3 else None,
        )
        await mem.write_request(req)

    props = await nightshift._heuristic_skin_drift(mem, since, Config())
    await mem.shutdown()

    assert props, "Expected skin drift proposal"
    assert props[0]["heuristic"] == "skin_classification_drift"
    assert "tier-1" in props[0]["observation"]


@pytest.mark.asyncio
async def test_budget_calibration_heuristic_detects_red_pressure(tmp_path: Path) -> None:
    mem = SQLiteMemoryBackend(MemoryConfig(sqlite_path=str(tmp_path / "memory.db")))
    await mem.initialize()
    since = datetime.now(timezone.utc) - timedelta(hours=24)
    now = datetime.now(timezone.utc)

    for i in range(10):
        req = _make_req(
            request_id=f"req_{i}",
            ts=now,
            tier=2,
            final_decision="block" if i < 2 else "permit",
            block_reason="toe_red_denied" if i < 2 else None,
            cost_usd=0.02 if i >= 2 else 0.0,
        )
        await mem.write_request(req)

    props = await nightshift._heuristic_budget_calibration(mem, since, Config())
    await mem.shutdown()

    assert props, "Expected budget calibration proposal"
    assert props[0]["heuristic"] == "budget_calibration"
    assert "RED" in props[0]["title"]


def _make_req(*, request_id: str, ts: datetime, tier: int,
              final_decision: str, block_reason: str | None, cost_usd: float = 0.0):
    from tsukuyomi.core.types import CanonicalRequest, Credential, Decision, Message, Tier as ReqTier

    req = CanonicalRequest(
        request_id=request_id,
        inbound_format="openai",
        received_at=ts,
        model_requested="gpt-4o-mini",
        messages=[Message(role="user", content="x")],
        system_prompt=None,
        tools=[],
        max_tokens=128,
        temperature=1.0,
        stream=False,
        credential=Credential(raw_header="x", upstream_key="x", rewritten=False),
    )
    req.tier = ReqTier(tier)
    req.final_decision = Decision(final_decision)
    req.block_reason = block_reason
    req.cost_usd = cost_usd
    return req
