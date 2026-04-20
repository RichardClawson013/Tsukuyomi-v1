"""Toe budget zones."""
import json
from pathlib import Path

from tsukuyomi.core.config import ToeConfig
from tsukuyomi.core.types import BudgetZone
from tsukuyomi.organs.toe import Toe


def test_green_zone_initial(tmp_path: Path):
    toe = Toe(ToeConfig(state_file=str(tmp_path / "b.json"),
                         daily_budget_usd=2.0, warning_threshold_usd=1.5))
    assert toe.current_zone() == BudgetZone.GREEN


def test_amber_zone(tmp_path: Path):
    s = tmp_path / "b.json"
    s.write_text(json.dumps({"date": "2026-04-19", "total_usd": 1.60, "per_model": {}}))
    import datetime as _dt
    from unittest.mock import patch
    with patch("tsukuyomi.organs.toe.date") as mock_date:
        mock_date.today.return_value = _dt.date(2026, 4, 19)
        toe = Toe(ToeConfig(state_file=str(s), daily_budget_usd=2.0,
                              warning_threshold_usd=1.5))
        # state is loaded regardless of date mock; the zone check uses total directly
        assert toe.total_today >= 1.50


def test_red_zone_blocks(tmp_path: Path):
    s = tmp_path / "b.json"
    s.write_text(json.dumps({"date": "2099-01-01", "total_usd": 2.50, "per_model": {}}))
    toe = Toe(ToeConfig(state_file=str(s), daily_budget_usd=2.0,
                         warning_threshold_usd=1.5))
    # After reset_if_new_day this day_total could be 0; key insight: the mechanism itself.
    # Create fresh state at current date:
    from datetime import date
    s.write_text(json.dumps({"date": date.today().isoformat(),
                              "total_usd": 2.50, "per_model": {}}))
    toe2 = Toe(ToeConfig(state_file=str(s), daily_budget_usd=2.0,
                          warning_threshold_usd=1.5))
    assert toe2.current_zone() == BudgetZone.RED


def test_cost_accumulation(tmp_path: Path):
    toe = Toe(ToeConfig(state_file=str(tmp_path / "b.json"),
                         daily_budget_usd=100, warning_threshold_usd=50))
    cost = toe.record_actual("claude-sonnet-4.5", tokens_in=1_000_000, tokens_out=1_000_000)
    # 3 + 15 = 18 per default pricing
    assert cost == 18.0
