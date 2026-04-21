"""Shoulders blast-radius behavior with injectable GitNexus client."""
from __future__ import annotations

import pytest

from tsukuyomi.core.config import ShouldersConfig
from tsukuyomi.core.types import BlastRisk, Message, Tier
from tsukuyomi.organs.shoulders import Shoulders, StdioGitNexusClient


class _OkClient:
    def __init__(self, callers: int, files: list[str]) -> None:
        self.callers = callers
        self.files = files
        self.closed = False
        self.targets: list[str] = []

    async def get_impact(self, target: str) -> tuple[int, list[str]]:
        self.targets.append(target)
        return self.callers, self.files

    async def close(self) -> None:
        self.closed = True


class _FailClient:
    async def get_impact(self, target: str) -> tuple[int, list[str]]:
        del target
        raise RuntimeError("mcp unavailable")

    async def close(self) -> None:
        return None


@pytest.mark.asyncio
async def test_shoulders_uses_tool_call_symbol(minimal_config, fresh_canonical_request):
    cfg = minimal_config
    cfg.organs.shoulders = ShouldersConfig()
    client = _OkClient(callers=14, files=["a.py", "b.py"])
    shoulders = Shoulders(cfg.organs.shoulders, gitnexus_client=client)

    req = fresh_canonical_request(user_text="do it")
    req.messages.append(
        Message(
            role="assistant",
            content="",
            tool_calls=[{
                "name": "rename_symbol",
                "arguments": {"symbol": "process_order"},
            }],
        ),
    )
    req.tier = Tier.HIGH_RISK
    req.is_code_modifying = True

    await shoulders.analyze(req)

    assert req.blast_radius is not None
    assert req.blast_radius.target_symbol == "process_order"
    assert req.blast_radius.direct_callers == 14
    assert req.blast_radius.affected_files == ["a.py", "b.py"]
    assert req.blast_radius.risk == BlastRisk.HIGH
    assert client.targets == ["process_order"]


@pytest.mark.asyncio
async def test_shoulders_applies_thresholds(minimal_config, fresh_canonical_request):
    cfg = minimal_config
    cfg.organs.shoulders = ShouldersConfig(
        thresholds={
            "low_max_callers": 0,
            "medium_max_callers": 2,
            "high_max_callers": 4,
        },
    )
    client = _OkClient(callers=5, files=["x.py"])
    shoulders = Shoulders(cfg.organs.shoulders, gitnexus_client=client)

    req = fresh_canonical_request(user_text="rename process_order")
    req.tier = Tier.HIGH_RISK
    req.is_code_modifying = True
    await shoulders.analyze(req)

    assert req.blast_radius is not None
    assert req.blast_radius.risk == BlastRisk.CRITICAL


@pytest.mark.asyncio
async def test_shoulders_fallback_on_client_failure(minimal_config, fresh_canonical_request):
    cfg = minimal_config
    cfg.organs.shoulders = ShouldersConfig(unknown_treated_as="HIGH")
    shoulders = Shoulders(cfg.organs.shoulders, gitnexus_client=_FailClient())

    req = fresh_canonical_request(user_text="rename process_order")
    req.tier = Tier.HIGH_RISK
    req.is_code_modifying = True
    await shoulders.analyze(req)

    assert req.blast_radius is not None
    assert req.blast_radius.risk == BlastRisk.HIGH
    assert req.blast_radius.target_symbol == "process_order"


@pytest.mark.asyncio
async def test_shoulders_unknown_target_when_no_symbol(minimal_config, fresh_canonical_request):
    cfg = minimal_config
    cfg.organs.shoulders = ShouldersConfig()
    client = _OkClient(callers=99, files=["should-not-be-used.py"])
    shoulders = Shoulders(cfg.organs.shoulders, gitnexus_client=client)

    req = fresh_canonical_request(user_text="please improve this")
    req.tier = Tier.HIGH_RISK
    req.is_code_modifying = True
    await shoulders.analyze(req)

    assert req.blast_radius is not None
    assert req.blast_radius.risk == BlastRisk.UNKNOWN
    assert req.blast_radius.target_symbol == "unknown_target"
    assert client.targets == []


@pytest.mark.asyncio
async def test_shoulders_shutdown_closes_client(minimal_config):
    cfg = minimal_config
    cfg.organs.shoulders = ShouldersConfig()
    client = _OkClient(callers=0, files=[])
    shoulders = Shoulders(cfg.organs.shoulders, gitnexus_client=client)

    await shoulders.shutdown()

    assert client.closed


def test_stdio_pick_tool_name_prefers_gitnexus_impact():
    tools = {
        "tools": [
            {"name": "other_tool"},
            {"name": "gitnexus_impact"},
            {"name": "symbol_impact"},
        ],
    }
    assert StdioGitNexusClient._pick_tool_name(tools) == "gitnexus_impact"


def test_stdio_parse_impact_from_structured_content():
    result = {"structuredContent": {"direct_callers": 7, "affected_files": ["a.py", "b.py"]}}
    callers, files = StdioGitNexusClient._parse_impact(result)
    assert callers == 7
    assert files == ["a.py", "b.py"]


def test_stdio_parse_impact_from_text_json():
    result = {
        "content": [
            {"type": "text", "text": "{\"impact_count\": 3, \"impacted_files\": [\"x.ts\"]}"},
        ],
    }
    callers, files = StdioGitNexusClient._parse_impact(result)
    assert callers == 3
    assert files == ["x.ts"]
