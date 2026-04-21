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
    rows = await _query_db(
        memory,
        """SELECT rounds_json FROM audits WHERE ts_utc >= ?""",
        (since.isoformat(),),
    )
    phrase_counts: dict[str, int] = {}
    total_two_round_passes = 0

    for row in rows:
        rounds_raw = row.get("rounds_json")
        if not isinstance(rounds_raw, str):
            continue
        try:
            rounds = json.loads(rounds_raw)
        except json.JSONDecodeError:
            continue
        if not isinstance(rounds, list) or len(rounds) < 2:
            continue
        r1 = rounds[0] if isinstance(rounds[0], dict) else {}
        r2 = rounds[1] if isinstance(rounds[1], dict) else {}
        if bool(r1.get("approved")):
            continue
        if not bool(r2.get("approved")):
            continue
        total_two_round_passes += 1
        for reason in r1.get("reasons", []):
            if isinstance(reason, str) and reason.startswith("evasion_phrase:"):
                phrase = reason.split(":", 1)[1].strip()
                if phrase:
                    phrase_counts[phrase] = phrase_counts.get(phrase, 0) + 1

    proposals = []
    for phrase, count in sorted(phrase_counts.items(), key=lambda x: x[1], reverse=True):
        if count < 2:
            continue
        proposals.append({
            "slug": f"audit_evasion_{_slugify(phrase)}",
            "heuristic": "audit_evasion_patterns",
            "title": f"Review Gary evasion phrase handling: '{phrase}'",
            "observation": (
                f"Evasion phrase `{phrase}` appeared {count} times in round-1 failed audits "
                f"that subsequently passed round 2."
            ),
            "recommendation": (
                "Review whether this phrase should remain in the evasion list or if prompts/"
                "feedback need tuning to reduce repeated round-1 failures."
            ),
            "evidence_count": count,
            "metadata": {"two_round_passes": total_two_round_passes},
        })
    return proposals


async def _heuristic_skin_drift(memory, since, config) -> list[dict[str, Any]]:
    rows = await _query_db(
        memory,
        """
        SELECT tier, final_decision, block_reason, COUNT(*) AS n
        FROM requests
        WHERE ts_start_utc >= ?
        GROUP BY tier, final_decision, block_reason
        """,
        (since.isoformat(),),
    )
    tier1_total = 0
    tier1_risky = 0
    for row in rows:
        tier = row.get("tier")
        if tier != 1:
            continue
        n = int(row.get("n") or 0)
        tier1_total += n
        decision = str(row.get("final_decision") or "")
        reason = str(row.get("block_reason") or "")
        if decision == "block" and (
            reason.startswith("knee:")
            or reason.startswith("gary_")
            or reason.startswith("sandbox_")
            or reason.startswith("eyes_")
        ):
            tier1_risky += n

    if tier1_total == 0:
        return []
    ratio = tier1_risky / tier1_total
    if ratio < 0.10:
        return []

    return [{
        "slug": "skin_drift_tier1_risky_outcomes",
        "heuristic": "skin_classification_drift",
        "title": "Investigate Skin tier-1 drift toward risky outcomes",
        "observation": (
            f"{tier1_risky}/{tier1_total} tier-1 requests ({ratio:.1%}) ended in high-risk style "
            "blocks (knee/gary/sandbox/eyes indicators)."
        ),
        "recommendation": (
            "Review skin rules and default tier behavior. Consider promoting ambiguous tier-1-like "
            "prompts to tier 2 for stricter downstream checks."
        ),
        "evidence_count": tier1_risky,
    }]


async def _heuristic_budget_calibration(memory, since, config) -> list[dict[str, Any]]:
    rows = await _query_db(
        memory,
        """
        SELECT final_decision, block_reason, cost_usd
        FROM requests
        WHERE ts_start_utc >= ?
        """,
        (since.isoformat(),),
    )
    total = len(rows)
    if total == 0:
        return []

    toe_red_blocks = 0
    expensive = 0
    spend = 0.0
    for row in rows:
        spend += float(row.get("cost_usd") or 0.0)
        if str(row.get("block_reason") or "") == "toe_red_denied":
            toe_red_blocks += 1
        if float(row.get("cost_usd") or 0.0) >= 0.10:
            expensive += 1

    red_ratio = toe_red_blocks / total
    expensive_ratio = expensive / total

    proposals: list[dict[str, Any]] = []
    if red_ratio >= 0.10:
        proposals.append({
            "slug": "budget_calibration_tight_red_hits",
            "heuristic": "budget_calibration",
            "title": "Budget frequently hits RED zone",
            "observation": (
                f"Toe RED denials occurred {toe_red_blocks}/{total} requests ({red_ratio:.1%}) in "
                "the lookback window."
            ),
            "recommendation": (
                "Review daily budget and warning threshold values. Consider a slightly higher daily "
                "budget or earlier downgrade mapping to reduce hard-stop frequency."
            ),
            "evidence_count": toe_red_blocks,
            "metadata": {"total_spend_usd": round(spend, 4)},
        })
    elif expensive_ratio >= 0.30:
        proposals.append({
            "slug": "budget_calibration_high_cost_density",
            "heuristic": "budget_calibration",
            "title": "High density of expensive requests",
            "observation": (
                f"{expensive}/{total} requests ({expensive_ratio:.1%}) cost >= $0.10 each."
            ),
            "recommendation": (
                "Tune Toe downgrade_map so expensive models downgrade earlier in AMBER zone."
            ),
            "evidence_count": expensive,
            "metadata": {"total_spend_usd": round(spend, 4)},
        })
    return proposals


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


def _slugify(value: str) -> str:
    out = "".join(ch.lower() if ch.isalnum() else "_" for ch in value).strip("_")
    while "__" in out:
        out = out.replace("__", "_")
    return out or "item"


async def _query_db(memory: SQLiteMemoryBackend, sql: str,
                    params: tuple[Any, ...]) -> list[dict[str, Any]]:
    db = memory._db  # shared backend in same process; NightShift is read-only.
    if db is None:
        return []
    async with db.execute(sql, params) as cur:
        cols = [d[0] for d in cur.description]
        return [dict(zip(cols, row)) async for row in cur]


def main_cli() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True)
    parser.add_argument("--lookback-hours", type=int, default=24)
    args = parser.parse_args()
    return asyncio.run(run_nightshift(args.config, args.lookback_hours))


if __name__ == "__main__":
    raise SystemExit(main_cli())
