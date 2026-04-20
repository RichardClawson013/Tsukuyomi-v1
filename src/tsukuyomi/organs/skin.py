"""Skin / Huid — input tier classifier.

Spec: docs/architecture/03_organs.md §4.1.
"""
from __future__ import annotations
import json
import re
from pathlib import Path
from typing import Any

from tsukuyomi.core.types import CanonicalRequest, Tier
from tsukuyomi.observability.logging import get_logger

log = get_logger(__name__)


_DEFAULT_TIER3_PATTERNS = [
    r"\brm\s+-[rf]+\b", r"\bdrop\s+table\b", r"\bforce\s+push\b",
    r"\breset\s+--hard\b", r"\bdelete\s+branch\b", r"\btruncate\s+table\b",
    r"\brevert\s+.*\s+--no-edit\b", r"\bmigrate\s+.*\s+down\b",
    r"\bdd\s+if=\S+\s+of=/dev", r"\bmkfs\.",
]

_DEFAULT_TIER2_PATTERNS = [
    r"\bedit\s+\S+\.(py|ts|js|rs|go|java|c|cpp|h|hpp)\b",
    r"\bwrite\s+to\b", r"\bcreate\s+file\b", r"\bmodify\s+\S+\b",
    r"\bchmod\b", r"\bchown\b", r"\bmv\s+\S+\s+\S+\b",
]

_DEFAULT_TIER1_HINTS = [
    r"^(what|where|when|why|how|which|who|explain|show|list|read|describe)\b",
    r"\bshow me\b", r"\btell me about\b",
]

_CODE_WRITE_MARKERS = ["write", "edit", "modify", "create", "refactor", "rename",
                       "delete", "remove", "migrate", "drop"]


class Skin:
    def __init__(self, config: Any) -> None:
        self.config = config
        self.tier3_patterns = [re.compile(p, re.IGNORECASE) for p in _DEFAULT_TIER3_PATTERNS]
        self.tier2_patterns = [re.compile(p, re.IGNORECASE) for p in _DEFAULT_TIER2_PATTERNS]
        self.tier1_hints = [re.compile(p, re.IGNORECASE) for p in _DEFAULT_TIER1_HINTS]
        rules_path = Path(getattr(config, "rules_file", "")).expanduser()
        if rules_path.exists():
            try:
                data = json.loads(rules_path.read_text())
                self.tier3_patterns += [re.compile(p, re.IGNORECASE) for p in data.get("tier3", [])]
                self.tier2_patterns += [re.compile(p, re.IGNORECASE) for p in data.get("tier2", [])]
            except Exception as exc:
                log.warning("skin.rules_load_failed", path=str(rules_path), error=str(exc))

    async def classify(self, req: CanonicalRequest) -> None:
        """Set req.tier, req.is_code_modifying, req.has_file_writes."""
        last_user_content = ""
        for m in reversed(req.messages):
            if m.role == "user":
                last_user_content = m.content or ""
                break
        aggregated = (last_user_content or "") + " " + (req.system_prompt or "")

        tier = Tier.ROUTINE
        matched_rule = None
        for pat in self.tier3_patterns:
            if pat.search(aggregated):
                tier = Tier.HIGH_RISK; matched_rule = pat.pattern; break
        if tier == Tier.ROUTINE:
            for pat in self.tier2_patterns:
                if pat.search(aggregated):
                    tier = Tier.ELEVATED; matched_rule = pat.pattern; break
        if tier == Tier.ROUTINE:
            any_tier1_hint = any(p.search(aggregated) for p in self.tier1_hints)
            if not any_tier1_hint:
                tier = Tier(int(getattr(self.config, "default_tier", 2)))

        req.tier = tier

        lower = aggregated.lower()
        req.is_code_modifying = any(m in lower for m in _CODE_WRITE_MARKERS)
        req.has_file_writes = req.is_code_modifying and tier.value >= 2

        log.info("skin.classify",
                 request_id=req.request_id,
                 tier=tier.value,
                 matched_rule_id=matched_rule,
                 classifier_confidence=None,
                 classifier_top_class=None)
