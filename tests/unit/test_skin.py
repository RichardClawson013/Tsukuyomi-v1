"""Skin tier classification."""
import pytest

from tsukuyomi.core.config import SkinConfig
from tsukuyomi.core.types import Tier
from tsukuyomi.organs.skin import Skin


@pytest.mark.asyncio
async def test_tier3_rm_rf(fresh_canonical_request):
    skin = Skin(SkinConfig())
    req = fresh_canonical_request(user_text="please run rm -rf /")
    await skin.classify(req)
    assert req.tier == Tier.HIGH_RISK


@pytest.mark.asyncio
async def test_tier3_drop_table(fresh_canonical_request):
    skin = Skin(SkinConfig())
    req = fresh_canonical_request(user_text="run DROP TABLE users; on the prod db")
    await skin.classify(req)
    assert req.tier == Tier.HIGH_RISK


@pytest.mark.asyncio
async def test_tier1_simple_question(fresh_canonical_request):
    skin = Skin(SkinConfig())
    req = fresh_canonical_request(user_text="what is in this file?")
    await skin.classify(req)
    assert req.tier == Tier.ROUTINE


@pytest.mark.asyncio
async def test_tier2_edit(fresh_canonical_request):
    skin = Skin(SkinConfig())
    req = fresh_canonical_request(user_text="edit main.py to add a logger")
    await skin.classify(req)
    assert req.tier == Tier.ELEVATED
