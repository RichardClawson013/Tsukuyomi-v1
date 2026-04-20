"""Protocol Gary deterministic validation rules."""
from tsukuyomi.core.config import GaryConfig
from tsukuyomi.protocols.gary import ProtocolGary


def test_evasion_phrase_fails():
    gary = ProtocolGary(GaryConfig())
    answers = {
        "Q1": "a" * 200, "Q2": "b" * 200, "Q3": "c" * 200,
        "Q4": "this is perfectly safe, nothing will go wrong" + "x" * 100,
        "Q5": "d" * 100,
    }
    result = gary._validate(answers)
    assert not result["approved"]
    assert any("evasion_phrase" in r for r in result["reasons"])


def test_too_short_fails():
    gary = ProtocolGary(GaryConfig())
    answers = {"Q1": "short", "Q2": "x", "Q3": "x", "Q4": "x", "Q5": "x"}
    result = gary._validate(answers)
    assert not result["approved"]
    assert any("too_short" in r for r in result["reasons"])


def test_valid_answers_pass():
    gary = ProtocolGary(GaryConfig())
    # Craft answers that satisfy length, evasion, risk-vocab, concreteness
    answers = {
        "Q1": ("If the migration_v42.py script fails halfway through, "
               "we leave the users table in a corrupt state with null "
               "foreign keys that could crash the payment service at "
               "/app/services/billing.py and cause data loss for "
               "in-flight orders. This is irreversible without a backup."),
        "Q2": "Scenario 1: users table. Scenario 2: billing.py service. Scenario 3: customers_table in db.",
        "Q3": ("I'm not verifying /backup/users-2026.sql exists before "
               "starting. I'm not checking the lock on orders_table.pk. "
               "I'm not validating 42-character VARCHAR limits."),
        "Q4": ("1: pre-migration backup check via /backup/last.sql needs "
               "review. 2: rollback procedure named reset_migration_v42 "
               "has not been tested end-to-end, race condition risk."),
        "Q5": "Refuse if /backup/last.sql is older than 24 hours or missing.",
    }
    result = gary._validate(answers)
    assert result["approved"], f"Should pass, reasons: {result['reasons']}"
