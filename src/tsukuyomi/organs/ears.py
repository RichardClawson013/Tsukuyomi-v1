"""Ears — ambiguity detection.

Spec: docs/architecture/03_organs.md §4.2.
"""
from __future__ import annotations
import re
from dataclasses import dataclass, field
from typing import Any

from tsukuyomi.core.types import CanonicalRequest
from tsukuyomi.observability.logging import get_logger

log = get_logger(__name__)


@dataclass
class AmbiguityVerdict:
    clear: bool
    reasons: list[str] = field(default_factory=list)


_PRONOUNS = {"it", "that", "this", "them", "those", "these"}
_ACTION_VERBS_NO_OBJECT = re.compile(r"\b(fix|clean|update|refactor|change|remove|delete)\b(?!\s+(?:the|my|all|any)?\s*\w+)", re.IGNORECASE)
_SCOPE_UNBOUNDED = re.compile(r"\b(all|every|everything)\b", re.IGNORECASE)


class Ears:
    def __init__(self, config: Any) -> None:
        self.config = config

    async def evaluate(self, req: CanonicalRequest) -> AmbiguityVerdict:
        reasons: list[str] = []
        text = ""
        for m in reversed(req.messages):
            if m.role == "user":
                text = m.content or ""; break

        checks = getattr(self.config, "checks", {})

        if checks.get("pronoun_resolution", True):
            words = set(re.findall(r"[A-Za-z']+", text.lower()))
            if _PRONOUNS & words:
                context = " ".join((m.content or "") for m in req.messages[-4:])
                if len(context) < 80:
                    reasons.append("pronoun_without_antecedent")

        if checks.get("verb_object_fit", True):
            if _ACTION_VERBS_NO_OBJECT.search(text):
                reasons.append("action_verb_missing_object")

        if checks.get("scope_indicators", True):
            if _SCOPE_UNBOUNDED.search(text) and req.tier and req.tier.value >= 2:
                reasons.append("unbounded_scope_on_tier2plus")

        clear = not reasons
        log.info("ears.evaluate",
                 request_id=req.request_id,
                 verdict=("clear" if clear else "ambiguous"),
                 triggered_checks=reasons)
        return AmbiguityVerdict(clear=clear, reasons=reasons)
