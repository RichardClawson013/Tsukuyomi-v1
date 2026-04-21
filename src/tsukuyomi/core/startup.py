"""Top-level startup — wires together all components and runs the server."""
from __future__ import annotations
import asyncio
import os
from pathlib import Path
from typing import Optional

from tsukuyomi.core.config import Config, load_config
from tsukuyomi.core.nervecore import AsyncioNerveCore
from tsukuyomi.core.arbiter import Arbiter
from tsukuyomi.observability.logging import configure_logging, get_logger
from tsukuyomi.memory.sqlite_backend import SQLiteMemoryBackend
from tsukuyomi.organs.skin import Skin
from tsukuyomi.organs.ears import Ears
from tsukuyomi.organs.shoulders import Shoulders
from tsukuyomi.organs.knee import Knee
from tsukuyomi.organs.toe import Toe
from tsukuyomi.organs.eyes import Eyes
from tsukuyomi.organs.nose import Nose
from tsukuyomi.organs.mouth import Mouth
from tsukuyomi.organs.sandbox.worktree_backend import WorktreeSandboxBackend
from tsukuyomi.protocols.gary import ProtocolGary
from tsukuyomi.interceptor.server import InterceptorServer


async def start(config_path: Optional[str | Path] = None) -> None:
    """Start the Tsukuyomi service.

    Returns when the service is shut down.
    """
    if config_path is None:
        config_path = _default_config_path()
    config = load_config(config_path)
    configure_logging(config.observability)
    log = get_logger(__name__)
    log.info("starting", version="1.0.0", config=str(config_path))

    nerve = AsyncioNerveCore()
    await nerve.start()

    memory = SQLiteMemoryBackend(config.memory)
    await memory.initialize()

    skin = Skin(config.organs.skin)
    ears = Ears(config.organs.ears)
    shoulders = Shoulders(config.organs.shoulders)
    knee = Knee(config.organs.knee)
    toe = Toe(config.organs.toe)
    eyes = Eyes(config.organs.eyes)
    nose = Nose(config.organs.nose, nerve)
    mouth = Mouth(config.organs.mouth)
    sandbox = WorktreeSandboxBackend()
    gary = ProtocolGary(config.protocols.gary)

    arbiter = Arbiter(
        config=config, nerve=nerve, memory=memory,
        skin=skin, ears=ears, shoulders=shoulders,
        knee=knee, toe=toe, eyes=eyes, nose=nose, mouth=mouth,
        sandbox=sandbox, gary=gary,
    )

    server = InterceptorServer(config.interceptor, config.upstream, arbiter)
    log.info("listening", host=config.interceptor.host, port=config.interceptor.port)
    try:
        await server.serve_forever()
    finally:
        await shoulders.shutdown()
        await memory.shutdown()
        await nerve.shutdown()
        log.info("stopped")


def _default_config_path() -> Path:
    xdg = os.environ.get("XDG_DATA_HOME") or str(Path.home() / ".local/share")
    return Path(xdg) / "tsukuyomi" / "config" / "corelaw.json"
