"""Integration: tier-1 request flows through permit path quickly."""
import asyncio
import pytest

from tsukuyomi.core.arbiter import Arbiter
from tsukuyomi.core.nervecore import AsyncioNerveCore
from tsukuyomi.core.types import CanonicalRequest, Credential, Decision, Message
from tsukuyomi.memory.sqlite_backend import SQLiteMemoryBackend
from tsukuyomi.organs import Skin, Ears, Shoulders, Knee, Toe, Eyes, Nose, Mouth
from tsukuyomi.organs.sandbox.worktree_backend import WorktreeSandboxBackend
from tsukuyomi.protocols.gary import ProtocolGary


@pytest.mark.asyncio
async def test_tier1_permitted(minimal_config, fresh_canonical_request):
    cfg = minimal_config
    nerve = AsyncioNerveCore()
    await nerve.start()
    mem = SQLiteMemoryBackend(cfg.memory)
    await mem.initialize()

    arbiter = Arbiter(
        config=cfg, nerve=nerve, memory=mem,
        skin=Skin(cfg.organs.skin), ears=Ears(cfg.organs.ears),
        shoulders=Shoulders(cfg.organs.shoulders), knee=Knee(cfg.organs.knee),
        toe=Toe(cfg.organs.toe), eyes=Eyes(cfg.organs.eyes),
        nose=Nose(cfg.organs.nose, nerve), mouth=Mouth(cfg.organs.mouth),
        sandbox=WorktreeSandboxBackend(), gary=ProtocolGary(cfg.protocols.gary),
    )
    req = fresh_canonical_request(user_text="what does this file do?")
    result = await arbiter.process(req)
    assert result.final_decision == Decision.PERMIT
    await mem.shutdown(); await nerve.shutdown()
