"""NerveCore pub/sub."""
import asyncio
import pytest

from tsukuyomi.core.nervecore import AsyncioNerveCore, Signal


@pytest.mark.asyncio
async def test_publish_subscribe():
    nerve = AsyncioNerveCore()
    await nerve.start()
    received: list = []
    async def handler(sig):
        received.append(sig)
    nerve.subscribe("foo.*", handler)
    await nerve.publish(Signal(topic="foo.bar", payload={"x": 1}))
    await asyncio.sleep(0.1)
    await nerve.shutdown()
    assert len(received) == 1
    assert received[0].topic == "foo.bar"


@pytest.mark.asyncio
async def test_pattern_does_not_match_unrelated():
    nerve = AsyncioNerveCore()
    await nerve.start()
    received: list = []
    async def handler(sig):
        received.append(sig)
    nerve.subscribe("foo.*", handler)
    await nerve.publish(Signal(topic="bar.baz"))
    await asyncio.sleep(0.1)
    await nerve.shutdown()
    assert len(received) == 0
