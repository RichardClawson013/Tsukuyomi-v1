"""Tsukuyomi — Anatomic AI in Infinite Tsukuyomi.

A deterministic interceptor-layer that forces safety into any LLM agent,
by architecture rather than by prompting.

Public API:
    tsukuyomi.start()           — start the interceptor service
    tsukuyomi.Arbiter           — main orchestrator (programmatic use)
    tsukuyomi.config            — config loader

See README.md and docs/ for the full architecture.
"""

__version__ = "1.0.0"
__author__ = "Rob de Vet"
__license__ = "Apache-2.0"

from tsukuyomi.core.arbiter import Arbiter
from tsukuyomi.core.config import Config, load_config
from tsukuyomi.core.startup import start

__all__ = ["Arbiter", "Config", "load_config", "start", "__version__"]
