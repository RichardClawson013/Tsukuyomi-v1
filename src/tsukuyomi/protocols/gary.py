"""Protocol Gary — forced self-audit.

Spec: docs/architecture/04_protocols.md §5.1 and ADR 0004.
"""
from __future__ import annotations
import json
import re
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from tsukuyomi.core.types import CanonicalRequest, GaryVerdict
from tsukuyomi.observability.logging import get_logger

log = get_logger(__name__)


FIVE_QUESTIONS = [
    "List 3 specific things that could go wrong with this plan. "
    "Each must be a concrete failure scenario, not a general concern.",
    "Name the component, file, user, or system that would be hurt most "
    "if this fails. One name per scenario above.",
    "What are you *not* checking or verifying before executing? Minimum 2 blind spots.",
    "If someone else proposed this exact plan to you, name 2 reasons you would tell them to wait.",
    "Give a concrete condition — a specific threshold, file state, or environment — "
    "under which you would refuse, even if the user insists.",
]

DEFAULT_EVASION_PHRASES = [
    "nothing will go wrong", "no significant risk", "perfectly safe",
    "standard operation", "no concerns", "it's fine", "it is fine",
    "routine task", "well-tested", "no issues expected", "low-risk operation",
]

DEFAULT_RISK_KEYWORDS = [
    "break", "broken", "corrupt", "lose", "lost", "delete", "deleted",
    "destroy", "destruction", "irreversible", "permanent", "unrecoverable",
    "conflict", "race", "deadlock", "leak", "leakage", "expose", "exposure",
    "bypass", "crash", "hang", "escalate", "escalation", "privilege",
    "inject", "injection", "spoof", "spoofing", "stale", "staleness",
    "inconsistent", "orphan", "fail", "failure", "failed", "error",
    "exception", "undefined", "null", "nil", "starvation", "overflow",
    "underflow",
]


class ProtocolGary:
    def __init__(self, config: Any) -> None:
        self.config = config
        self.evasion = self._load_list(getattr(config, "evasion_phrases_file", ""),
                                        DEFAULT_EVASION_PHRASES)
        self.risk_kw = set(self._load_list(getattr(config, "risk_keywords_file", ""),
                                            DEFAULT_RISK_KEYWORDS))
        self.log_dir = Path(getattr(config, "audit_log_dir", "data/audits")).expanduser()
        self.log_dir.mkdir(parents=True, exist_ok=True)

    async def audit(self, req: CanonicalRequest) -> GaryVerdict:
        """Run 1 or 2 rounds of structured audit; return a verdict.

        For v1.0 the audit LLM call is abstracted through an `audit_executor`
        which defaults to an echo-stub for local-test; real deployments wire
        this to the configured upstream (Anthropic Haiku by default).
        """
        audit_id = f"aud_{uuid.uuid4().hex[:10]}"
        started = time.time()
        rounds: list[dict[str, Any]] = []
        action_summary = self._summarize_action(req)
        feedback = None
        passed = False
        total_cost = 0.0

        max_rounds = int(getattr(self.config, "max_rounds", 2))
        for r in range(1, max_rounds + 1):
            answers, cost = await self._ask_audit_llm(req, action_summary, feedback=feedback)
            total_cost += cost
            validation = self._validate(answers)
            rounds.append({
                "round": r,
                "questions": FIVE_QUESTIONS,
                "answers": answers,
                "approved": validation["approved"],
                "reasons": validation["reasons"],
            })
            if validation["approved"]:
                passed = True
                break
            feedback = validation["reasons"]

        verdict = GaryVerdict(
            audit_id=audit_id,
            rounds=rounds,
            final_decision=("PASS" if passed else "ESCALATED"),
            audit_cost_usd=round(total_cost, 5),
            audit_latency_seconds=round(time.time() - started, 2),
        )
        req.gary_verdict = verdict

        self._persist_audit(audit_id, req, action_summary, rounds, verdict)

        log.info("gary.audit_complete",
                 request_id=req.request_id, audit_id=audit_id,
                 final_decision=verdict.final_decision, rounds_count=len(rounds),
                 cost_usd=verdict.audit_cost_usd, latency_s=verdict.audit_latency_seconds)
        return verdict

    # ----- validation -----

    def _validate(self, answers: dict[str, str]) -> dict[str, Any]:
        reasons: list[str] = []
        lengths = getattr(self.config, "min_answer_lengths", {})
        for q in ("Q1", "Q2", "Q3", "Q4", "Q5"):
            got = len(answers.get(q, "").strip())
            need = int(lengths.get(q, 0))
            if got < need:
                reasons.append(f"{q}_too_short({got}<{need})")

        joined = " ".join(answers.values()).lower()
        for p in self.evasion:
            if p in joined:
                reasons.append(f"evasion_phrase:{p}")

        kw_hits = len({kw for kw in self.risk_kw if kw in joined})
        need_kw = int(getattr(self.config, "min_risk_keywords_total", 4))
        if kw_hits < need_kw:
            reasons.append(f"insufficient_risk_vocabulary({kw_hits}<{need_kw})")

        for q in ("Q1", "Q3", "Q4"):
            txt = answers.get(q, "")
            has_number = bool(re.search(r"\d", txt))
            has_path = "/" in txt or "." in txt
            has_ident = bool(re.search(r"[A-Z][a-z]+[A-Z]|[a-z]+_[a-z]+", txt))
            if not (has_number or has_path or has_ident):
                reasons.append(f"{q}_lacks_concreteness")

        return {"approved": not reasons, "reasons": reasons}

    # ----- audit LLM executor (stub) -----

    async def _ask_audit_llm(self, req: CanonicalRequest, action: str,
                              feedback: list[str] | None) -> tuple[dict[str, str], float]:
        """Stub: in production this dispatches to the configured audit endpoint.

        For v1.0 shipping, this stub returns empty answers which will fail
        validation, triggering escalation. Users must wire a real audit
        executor; see docs/guides/configuration.md §Gary.
        """
        answers = {q: "" for q in ("Q1", "Q2", "Q3", "Q4", "Q5")}
        # 0 cost when stubbed
        return answers, 0.0

    def _summarize_action(self, req: CanonicalRequest) -> str:
        for m in reversed(req.messages):
            if m.role == "user":
                return (m.content or "")[:200]
        return ""

    def _persist_audit(self, audit_id: str, req: CanonicalRequest,
                       summary: str, rounds: list[dict[str, Any]],
                       verdict: GaryVerdict) -> None:
        month = datetime.now(timezone.utc).strftime("%Y-%m")
        target = self.log_dir / month
        target.mkdir(parents=True, exist_ok=True)
        record = {
            "audit_id": audit_id,
            "request_id": req.request_id,
            "ts_utc": datetime.now(timezone.utc).isoformat(),
            "action_summary": summary,
            "triggering_organ": "gary",
            "rounds": rounds,
            "final_decision": verdict.final_decision,
            "audit_cost_usd": verdict.audit_cost_usd,
            "audit_latency_seconds": verdict.audit_latency_seconds,
        }
        (target / f"{audit_id}.json").write_text(json.dumps(record, indent=2))

    @staticmethod
    def _load_list(path_str: str, fallback: list[str]) -> list[str]:
        p = Path(path_str).expanduser() if path_str else None
        if p and p.exists():
            try:
                data = json.loads(p.read_text())
                if isinstance(data, dict) and "items" in data:
                    return list(data["items"])
                if isinstance(data, list):
                    return data
            except Exception:
                pass
        return list(fallback)
