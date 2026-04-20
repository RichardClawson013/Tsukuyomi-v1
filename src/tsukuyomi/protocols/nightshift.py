"""NightShift — offline pattern-mining of Tsukuyomi's own logs.

Spec: docs/architecture/04_protocols.md §5.2.
Human-in-the-loop required. NEVER auto-applies proposals.
"""
from __future__ import annotations
import argparse
import asyncio
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from tsukuyomi.core.config import load_config
from tsukuyomi.memory.sqlite_backend import SQLiteMemoryBackend
from tsukuyomi.observability.logging import configure_logging, get_logger


async def run_nightshift(config_path: str, lookback_hours: int = 24) -> int:
    config = load_config(config_path)
    configure_logging(config.observability)
    log = get_logger("nightshift")

    memory = SQLiteMemoryBackend(config.memory)
    await memory.initialize()

    since = datetime.now(timezone.utc) - timedelta(hours=lookback_hours)
    proposals_dir = Path(config.protocols.nightshift.proposals_dir).expanduser()
    today_dir = proposals_dir / datetime.now(timezone.utc).strftime("%Y-%m-%d")
    today_dir.mkdir(parents=True, exist_ok=True)

    proposals: list[Path] = []
    for name in config.protocols.nightshift.heuristics_enabled:
        heuristic = HEURISTICS.get(name)
        if not heuristic:
            log.warning("nightshift.unknown_heuristic", name=name)
            continue
        result = await heuristic(memory, since, config)
        for prop in result:
            p = today_dir / f"{prop['slug']}.md"
            p.write_text(_render_proposal(prop))
            proposals.append(p)
            log.info("nightshift.proposal", heuristic=name, path=str(p))

    await memory.shutdown()
    log.info("nightshift.complete", proposals_generated=len(proposals))
    return len(proposals)


async def _heuristic_frequently_blocked(memory, since, config) -> list[dict[str, Any]]:
    events = await memory.query_events(since_iso=since.isoformat(),
                                        organ="knee", decision="block")
    counts: dict[str, int] = {}
    for e in events:
        try:
            meta = json.loads(e.get("metadata_json") or "{}")
            pid = meta.get("matched_pattern_id") or "unknown"
        except Exception:
            pid = "unknown"
        counts[pid] = counts.get(pid, 0) + 1

    min_count = config.protocols.nightshift.min_block_count_for_proposal
    proposals = []
    for pid, n in counts.items():
        if n >= min_count:
            proposals.append({
                "slug": f"frequently_blocked_{pid}",
                "heuristic": "frequently_blocked_commands",
                "title": f"Widen or review Knee pattern: {pid}",
                "observation": f"The Knee blocked pattern `{pid}` {n} times in the last lookback window.",
                "recommendation": "Review events, confirm whether the pattern is genuinely destructive or if a legitimate variant is being caught.",
                "evidence_count": n,
            })
    return proposals


async def _heuristic_audit_evasion(memory, since, config) -> list[dict[str, Any]]:
    # Stub — queries audits table for round-1-fail-round-2-pass patterns.
    return []


async def _heuristic_skin_drift(memory, since, config) -> list[dict[str, Any]]:
    return []


async def _heuristic_budget_calibration(memory, since, config) -> list[dict[str, Any]]:
    return []


async def _heuristic_nose_threshold(memory, since, config) -> list[dict[str, Any]]:
    return []


async def _heuristic_sandbox_mismatches(memory, since, config) -> list[dict[str, Any]]:
    return []


async def _heuristic_gitnexus_staleness(memory, since, config) -> list[dict[str, Any]]:
    return []


HEURISTICS = {
    "frequently_blocked_commands": _heuristic_frequently_blocked,
    "audit_evasion_patterns": _heuristic_audit_evasion,
    "skin_classification_drift": _heuristic_skin_drift,
    "budget_calibration": _heuristic_budget_calibration,
    "nose_threshold_calibration": _heuristic_nose_threshold,
    "untriggered_sandbox_mismatches": _heuristic_sandbox_mismatches,
    "gitnexus_staleness": _heuristic_gitnexus_staleness,
}


def _render_proposal(prop: dict[str, Any]) -> str:
    return f"""# Proposal: {prop['title']}

**Heuristic:** `{prop['heuristic']}`
**Generated:** {datetime.now(timezone.utc).isoformat()}

## Observation

{prop['observation']}

## Evidence

- Count: {prop.get('evidence_count', 'n/a')}

## Recommendation

{prop['recommendation']}

## Status

`pending` — human review required before any configuration change.

---

*NightShift never auto-applies. See docs/architecture/04_protocols.md §5.2.*
"""


def main_cli() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True)
    parser.add_argument("--lookback-hours", type=int, default=24)
    args = parser.parse_args()
    return asyncio.run(run_nightshift(args.config, args.lookback_hours))


if __name__ == "__main__":
    raise SystemExit(main_cli())
