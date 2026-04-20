"""Protocol Gary — forced self-audit.

Spec: docs/architecture/04_protocols.md §5.1 and ADR 0004.
"""
from __future__ import annotations
from dataclasses import dataclass
import json
import os
import re
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Protocol

import httpx
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


class AuditExecutor(Protocol):
    async def ask(
        self,
        *,
        req: CanonicalRequest,
        action: str,
        feedback: list[str] | None,
        questions: list[str],
    ) -> tuple[dict[str, str], float]:
        """Return (answers, estimated_usd_cost)."""


class StubAuditExecutor:
    async def ask(
        self,
        *,
        req: CanonicalRequest,
        action: str,
        feedback: list[str] | None,
        questions: list[str],
    ) -> tuple[dict[str, str], float]:
        del req, action, feedback, questions
        # Deterministic safe default: forces validation failure and escalation.
        return {q: "" for q in ("Q1", "Q2", "Q3", "Q4", "Q5")}, 0.0


@dataclass
class _AuditEndpoint:
    base_url: str
    model: str
    api_key_env_var: str | None
    timeout_seconds: int
    max_retries: int
    temperature: float
    input_per_million_usd: float
    output_per_million_usd: float


class HttpAuditExecutor:
    def __init__(self, primary: _AuditEndpoint, fallback: _AuditEndpoint | None = None) -> None:
        self.primary = primary
        self.fallback = fallback

    async def ask(
        self,
        *,
        req: CanonicalRequest,
        action: str,
        feedback: list[str] | None,
        questions: list[str],
    ) -> tuple[dict[str, str], float]:
        del req
        prompt = self._build_prompt(action=action, feedback=feedback, questions=questions)
        try:
            return await self._ask_endpoint(self.primary, prompt)
        except Exception as primary_exc:
            if self.fallback is None:
                raise primary_exc
            log.warning("gary.audit_primary_failed", error=str(primary_exc))
            return await self._ask_endpoint(self.fallback, prompt)

    async def _ask_endpoint(self, endpoint: _AuditEndpoint, prompt: str) -> tuple[dict[str, str], float]:
        url = f"{endpoint.base_url.rstrip('/')}/chat/completions"
        headers = {"content-type": "application/json"}
        if endpoint.api_key_env_var:
            key = os.environ.get(endpoint.api_key_env_var)
            if not key:
                raise RuntimeError(f"Missing env var: {endpoint.api_key_env_var}")
            headers["authorization"] = f"Bearer {key}"

        body = {
            "model": endpoint.model,
            "temperature": endpoint.temperature,
            "messages": [
                {"role": "system", "content": (
                    "You are Protocol Gary's audit model. "
                    "Return ONLY valid JSON object with string fields Q1..Q5."
                )},
                {"role": "user", "content": prompt},
            ],
            "response_format": {"type": "json_object"},
        }

        last_exc: Exception | None = None
        for attempt in range(endpoint.max_retries + 1):
            try:
                async with httpx.AsyncClient(timeout=float(endpoint.timeout_seconds)) as client:
                    resp = await client.post(url, headers=headers, json=body)
                resp.raise_for_status()
                payload = resp.json()
                answers = self._parse_answers(payload)
                return answers, self._estimate_cost(payload, endpoint)
            except Exception as exc:  # noqa: BLE001
                last_exc = exc
                if attempt < endpoint.max_retries:
                    continue
        if last_exc is None:
            raise RuntimeError("Unexpected audit executor failure")
        raise last_exc

    @staticmethod
    def _build_prompt(action: str, feedback: list[str] | None, questions: list[str]) -> str:
        feedback_text = "\n".join(f"- {r}" for r in (feedback or []))
        return (
            "Action summary:\n"
            f"{action}\n\n"
            "Questions (answer all, each as Q1..Q5):\n"
            f"Q1: {questions[0]}\n"
            f"Q2: {questions[1]}\n"
            f"Q3: {questions[2]}\n"
            f"Q4: {questions[3]}\n"
            f"Q5: {questions[4]}\n\n"
            "If prior round failed, address these validation issues explicitly:\n"
            f"{feedback_text or '- none'}\n\n"
            "Return JSON exactly like: "
            "{\"Q1\":\"...\",\"Q2\":\"...\",\"Q3\":\"...\",\"Q4\":\"...\",\"Q5\":\"...\"}"
        )

    @staticmethod
    def _parse_answers(payload: dict[str, Any]) -> dict[str, str]:
        choices = payload.get("choices") or []
        if not choices:
            raise ValueError("Audit response missing choices")
        message = choices[0].get("message") or {}
        content = message.get("content", "")
        if isinstance(content, list):
            content = "\n".join(
                p.get("text", "") if isinstance(p, dict) else str(p)
                for p in content
            )
        data = HttpAuditExecutor._parse_json_object(str(content))
        return {
            "Q1": str(data.get("Q1", "")),
            "Q2": str(data.get("Q2", "")),
            "Q3": str(data.get("Q3", "")),
            "Q4": str(data.get("Q4", "")),
            "Q5": str(data.get("Q5", "")),
        }

    @staticmethod
    def _parse_json_object(raw: str) -> dict[str, Any]:
        try:
            data = json.loads(raw)
            if isinstance(data, dict):
                return data
        except json.JSONDecodeError:
            pass
        match = re.search(r"\{.*\}", raw, re.DOTALL)
        if not match:
            raise ValueError("Audit response did not contain JSON object")
        parsed = json.loads(match.group(0))
        if not isinstance(parsed, dict):
            raise ValueError("Audit response JSON is not an object")
        return parsed

    @staticmethod
    def _estimate_cost(payload: dict[str, Any], endpoint: _AuditEndpoint) -> float:
        usage = payload.get("usage") or {}
        prompt_toks = int(usage.get("prompt_tokens") or 0)
        completion_toks = int(usage.get("completion_tokens") or 0)
        cost = (
            (prompt_toks / 1_000_000) * float(endpoint.input_per_million_usd)
            + (completion_toks / 1_000_000) * float(endpoint.output_per_million_usd)
        )
        return float(cost)


class ProtocolGary:
    def __init__(self, config: Any, audit_executor: AuditExecutor | None = None) -> None:
        self.config = config
        self.evasion = self._load_list(getattr(config, "evasion_phrases_file", ""),
                                        DEFAULT_EVASION_PHRASES)
        self.risk_kw = set(self._load_list(getattr(config, "risk_keywords_file", ""),
                                            DEFAULT_RISK_KEYWORDS))
        self.log_dir = Path(getattr(config, "audit_log_dir", "data/audits")).expanduser()
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.audit_executor: AuditExecutor = audit_executor or self._build_executor()

    async def audit(self, req: CanonicalRequest) -> GaryVerdict:
        """Run 1..N rounds of structured audit; return a verdict."""
        audit_id = f"aud_{uuid.uuid4().hex[:10]}"
        started = time.time()
        rounds: list[dict[str, Any]] = []
        action_summary = self._summarize_action(req)
        feedback = None
        passed = False
        total_cost = 0.0
        max_cost = float(getattr(self.config, "max_cost_per_audit_usd", 0.10))

        max_rounds = int(getattr(self.config, "max_rounds", 2))
        for r in range(1, max_rounds + 1):
            answers, cost, executor_error = await self._ask_audit_llm(
                req,
                action_summary,
                feedback=feedback,
            )
            total_cost += cost
            validation = self._validate(answers)
            if executor_error:
                validation["reasons"].append(f"audit_executor_error:{executor_error}")
            cost_cap_hit = total_cost > max_cost
            if cost_cap_hit:
                validation["reasons"].append(
                    f"cost_cap_exceeded({total_cost:.5f}>{max_cost:.5f})",
                )
                validation["approved"] = False
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
            if cost_cap_hit:
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
                              feedback: list[str] | None) -> tuple[dict[str, str], float, str | None]:
        try:
            answers, cost = await self.audit_executor.ask(
                req=req,
                action=action,
                feedback=feedback,
                questions=FIVE_QUESTIONS,
            )
            return answers, cost, None
        except Exception as exc:  # noqa: BLE001
            log.warning("gary.audit_executor_error", error=str(exc))
            answers = {q: "" for q in ("Q1", "Q2", "Q3", "Q4", "Q5")}
            reason = f"{exc.__class__.__name__}:{str(exc)[:120]}"
            return answers, 0.0, reason

    def _build_executor(self) -> AuditExecutor:
        base_url = getattr(self.config, "audit_http_base_url", None)
        if not base_url:
            log.info("gary.audit_executor_stub_enabled", reason="audit_http_base_url_not_configured")
            return StubAuditExecutor()

        primary = _AuditEndpoint(
            base_url=str(base_url),
            model=str(getattr(self.config, "audit_http_model", "gpt-4o-mini")),
            api_key_env_var=getattr(self.config, "audit_http_api_key_env_var", None),
            timeout_seconds=int(getattr(self.config, "audit_timeout_seconds", 20)),
            max_retries=int(getattr(self.config, "audit_max_retries", 1)),
            temperature=float(getattr(self.config, "audit_temperature", 0.0)),
            input_per_million_usd=float(getattr(self.config, "audit_input_per_million_usd", 0.0)),
            output_per_million_usd=float(getattr(self.config, "audit_output_per_million_usd", 0.0)),
        )

        fallback_model = getattr(self.config, "fallback_audit_http_model", None)
        fallback_base = getattr(self.config, "fallback_audit_http_base_url", None)
        fallback: _AuditEndpoint | None = None
        if fallback_model:
            fallback = _AuditEndpoint(
                base_url=str(fallback_base or base_url),
                model=str(fallback_model),
                api_key_env_var=(
                    getattr(self.config, "fallback_audit_http_api_key_env_var", None)
                    or getattr(self.config, "audit_http_api_key_env_var", None)
                ),
                timeout_seconds=int(getattr(self.config, "audit_timeout_seconds", 20)),
                max_retries=int(getattr(self.config, "audit_max_retries", 1)),
                temperature=float(getattr(self.config, "audit_temperature", 0.0)),
                input_per_million_usd=float(getattr(self.config, "audit_input_per_million_usd", 0.0)),
                output_per_million_usd=float(getattr(self.config, "audit_output_per_million_usd", 0.0)),
            )
        return HttpAuditExecutor(primary=primary, fallback=fallback)

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
