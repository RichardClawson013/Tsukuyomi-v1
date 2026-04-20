"""Structured JSON logging via structlog with mandatory key scrubbing.

ADR 0008. Every record passes through KeyScrubFilter before serialization.
"""
from __future__ import annotations
import logging
import re
import sys
from pathlib import Path
from typing import Any

import structlog


_API_KEY_PATTERNS = [
    re.compile(r"sk-ant-[A-Za-z0-9_-]{20,}"),
    re.compile(r"sk-[A-Za-z0-9_-]{20,}"),
    re.compile(r"sk-or-[A-Za-z0-9_-]{20,}"),
    re.compile(r"Bearer\s+[A-Za-z0-9._-]{20,}"),
]


def scrub_string(value: str) -> str:
    out = value
    for pat in _API_KEY_PATTERNS:
        out = pat.sub("[REDACTED:KEY]", out)
    return out


def _scrub_processor(logger, method_name, event_dict):  # noqa: ARG001
    for k, v in list(event_dict.items()):
        if isinstance(v, str):
            event_dict[k] = scrub_string(v)
        elif isinstance(v, dict):
            event_dict[k] = {kk: (scrub_string(vv) if isinstance(vv, str) else vv) for kk, vv in v.items()}
    return event_dict


def configure_logging(obs_config: Any) -> None:
    """Initialize structlog. Idempotent; safe to call multiple times."""
    log_level = getattr(logging, obs_config.log_level.upper(), logging.INFO)

    log_dir = Path(obs_config.log_dir).expanduser()
    log_dir.mkdir(parents=True, exist_ok=True)

    handlers = [logging.StreamHandler(sys.stderr)]
    file_handler = logging.FileHandler(log_dir / "anatomy.jsonl", encoding="utf-8")
    handlers.append(file_handler)

    logging.basicConfig(level=log_level, handlers=handlers, format="%(message)s", force=True)

    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.stdlib.add_log_level,
            structlog.processors.TimeStamper(fmt="iso", utc=True),
            _scrub_processor,
            structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.stdlib.BoundLogger,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )


def get_logger(name: str) -> structlog.stdlib.BoundLogger:
    return structlog.get_logger(name)
