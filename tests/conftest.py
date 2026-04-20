"""Shared fixtures."""
from __future__ import annotations
import asyncio
import sys
import tempfile
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


@pytest.fixture
def tmp_data_dir(tmp_path: Path) -> Path:
    (tmp_path / "data").mkdir()
    (tmp_path / "data" / "logs").mkdir()
    return tmp_path


@pytest.fixture
def minimal_config(tmp_data_dir: Path):
    from tsukuyomi.core.config import Config, MemoryConfig, ObservabilityConfig, ToeConfig, OrgansConfig
    cfg = Config()
    cfg.memory = MemoryConfig(sqlite_path=str(tmp_data_dir / "data/memory.db"))
    cfg.observability = ObservabilityConfig(log_dir=str(tmp_data_dir / "data/logs"))
    cfg.organs.toe = ToeConfig(state_file=str(tmp_data_dir / "data/budget_state.json"))
    return cfg


@pytest.fixture
def fresh_canonical_request():
    from datetime import datetime, timezone
    from tsukuyomi.core.types import CanonicalRequest, Credential, Message
    def _build(user_text: str = "hello", tier=None, code_modifying: bool = False,
               has_file_writes: bool = False):
        req = CanonicalRequest(
            request_id="req_test",
            inbound_format="anthropic",
            received_at=datetime.now(timezone.utc),
            model_requested="claude-sonnet-4.5",
            messages=[Message(role="user", content=user_text)],
            system_prompt=None,
            tools=[],
            max_tokens=1024,
            temperature=1.0,
            stream=False,
            credential=Credential(raw_header="x", upstream_key="x", rewritten=False),
        )
        if tier is not None:
            req.tier = tier
        req.is_code_modifying = code_modifying
        req.has_file_writes = has_file_writes
        return req
    return _build
