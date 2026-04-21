"""Protocol Gary audit execution paths (pass/escalate/error/cost-cap)."""
from __future__ import annotations

import pytest

from tsukuyomi.core.config import GaryConfig
from tsukuyomi.protocols.gary import ProtocolGary


def _valid_answers() -> dict[str, str]:
    return {
        "Q1": (
            "If migration_v42.py fails mid-run, users_table can become corrupt with null foreign "
            "keys and break billing_service.py. That failure is irreversible without a verified "
            "backup and could delete linkage needed for rollback."
        ),
        "Q2": (
            "Scenario 1: users_table. Scenario 2: billing_service.py. "
            "Scenario 3: customers_table in db/production.sqlite."
        ),
        "Q3": (
            "I'm not verifying /backups/users-2026.sql freshness. I'm not checking lock state on "
            "orders_table.pk. I'm not validating the 42-char VARCHAR boundary in migration_v42.py."
        ),
        "Q4": (
            "1: The reset_migration_v42 rollback path is untested and could fail under race "
            "conditions. 2: The script modifies users_table and risks inconsistent state if "
            "exceptions occur before transaction commit."
        ),
        "Q5": (
            "Refuse when /backups/users-2026.sql is missing, older than 24 hours, or checksum "
            "verification fails."
        ),
    }


class _PassingExecutor:
    async def ask(self, *, req, action, feedback, questions):
        del req, action, feedback, questions
        return _valid_answers(), 0.01


class _WeakThenGoodExecutor:
    def __init__(self) -> None:
        self.calls = 0
        self.feedback_seen: list[list[str] | None] = []

    async def ask(self, *, req, action, feedback, questions):
        del req, action, questions
        self.calls += 1
        self.feedback_seen.append(feedback)
        if self.calls == 1:
            return {q: "" for q in ("Q1", "Q2", "Q3", "Q4", "Q5")}, 0.0
        return _valid_answers(), 0.01


class _ErrorExecutor:
    async def ask(self, *, req, action, feedback, questions):
        del req, action, feedback, questions
        raise RuntimeError("simulated executor failure")


class _CostlyExecutor:
    async def ask(self, *, req, action, feedback, questions):
        del req, action, feedback, questions
        return _valid_answers(), 0.50


@pytest.mark.asyncio
async def test_audit_passes_with_real_answers(fresh_canonical_request, tmp_path):
    cfg = GaryConfig(audit_log_dir=str(tmp_path / "audits"))
    gary = ProtocolGary(cfg, audit_executor=_PassingExecutor())

    req = fresh_canonical_request(user_text="drop table users_legacy")
    verdict = await gary.audit(req)

    assert verdict.final_decision == "PASS"
    assert len(verdict.rounds) == 1
    assert verdict.audit_cost_usd == pytest.approx(0.01)


@pytest.mark.asyncio
async def test_audit_retries_then_passes(fresh_canonical_request, tmp_path):
    cfg = GaryConfig(audit_log_dir=str(tmp_path / "audits"))
    exec_ = _WeakThenGoodExecutor()
    gary = ProtocolGary(cfg, audit_executor=exec_)

    req = fresh_canonical_request(user_text="reset --hard and force push")
    verdict = await gary.audit(req)

    assert verdict.final_decision == "PASS"
    assert len(verdict.rounds) == 2
    assert exec_.feedback_seen[0] is None
    assert exec_.feedback_seen[1] is not None
    assert any("too_short" in r for r in exec_.feedback_seen[1] or [])


@pytest.mark.asyncio
async def test_executor_error_escalates(fresh_canonical_request, tmp_path):
    cfg = GaryConfig(audit_log_dir=str(tmp_path / "audits"))
    gary = ProtocolGary(cfg, audit_executor=_ErrorExecutor())

    req = fresh_canonical_request(user_text="drop table users")
    verdict = await gary.audit(req)

    assert verdict.final_decision == "ESCALATED"
    assert any(
        reason.startswith("audit_executor_error:RuntimeError")
        for reason in verdict.rounds[0]["reasons"]
    )


@pytest.mark.asyncio
async def test_cost_cap_escalates_even_when_answers_are_strong(
    fresh_canonical_request,
    tmp_path,
):
    cfg = GaryConfig(
        audit_log_dir=str(tmp_path / "audits"),
        max_cost_per_audit_usd=0.10,
    )
    gary = ProtocolGary(cfg, audit_executor=_CostlyExecutor())

    req = fresh_canonical_request(user_text="drop table users with no backup")
    verdict = await gary.audit(req)

    assert verdict.final_decision == "ESCALATED"
    assert any("cost_cap_exceeded" in r for r in verdict.rounds[0]["reasons"])
