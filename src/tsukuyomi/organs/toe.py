"""Toe — budget zone management.

Spec: docs/architecture/03_organs.md §4.5 and ADR on zones.
"""
from __future__ import annotations
import json
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any

from tsukuyomi.core.types import BudgetZone, CanonicalRequest
from tsukuyomi.observability.logging import get_logger

log = get_logger(__name__)


class Toe:
    def __init__(self, config: Any) -> None:
        self.config = config
        self.state_path = Path(getattr(config, "state_file", "data/budget_state.json")).expanduser()
        self.state_path.parent.mkdir(parents=True, exist_ok=True)
        self._state = self._load_state()
        self._pricing = self._load_pricing()

    @property
    def total_today(self) -> float:
        self._reset_if_new_day()
        return float(self._state.get("total_usd", 0.0))

    def current_zone(self) -> BudgetZone:
        t = self.total_today
        red = float(getattr(self.config, "daily_budget_usd", 2.00))
        amber = float(getattr(self.config, "warning_threshold_usd", 1.50))
        if t >= red:
            return BudgetZone.RED
        if t >= amber:
            return BudgetZone.AMBER
        return BudgetZone.GREEN

    async def evaluate(self, req: CanonicalRequest) -> str:
        zone = self.current_zone()
        req.toe_zone = zone
        req.model_used = req.model_requested

        if zone == BudgetZone.AMBER:
            downgrade_map = getattr(self.config, "downgrade_map", {}) or {}
            alt = downgrade_map.get(req.model_requested)
            if alt:
                req.model_used = alt
                log.info("toe.downgrade", request_id=req.request_id,
                         from_model=req.model_requested, to_model=alt,
                         zone="AMBER", total_usd_today=self.total_today)

        log.info("toe.evaluate",
                 request_id=req.request_id,
                 zone=zone.value, total_usd_today=self.total_today,
                 model_requested=req.model_requested, model_used=req.model_used,
                 downgraded=(req.model_used != req.model_requested))
        return zone.value

    def record_actual(self, model: str, tokens_in: int, tokens_out: int) -> float:
        """Post-call: record actual spend. Returns incremental cost."""
        pricing = self._pricing.get(model)
        if not pricing:
            return 0.0
        cost = (tokens_in / 1_000_000) * float(pricing.get("input_per_million_usd", 0)) + \
               (tokens_out / 1_000_000) * float(pricing.get("output_per_million_usd", 0))
        self._state["total_usd"] = self.total_today + cost
        self._state["date"] = date.today().isoformat()
        self._state.setdefault("per_model", {})
        self._state["per_model"][model] = self._state["per_model"].get(model, 0.0) + cost
        self._save_state()
        return cost

    def _load_state(self) -> dict[str, Any]:
        if not self.state_path.exists():
            return {"date": date.today().isoformat(), "total_usd": 0.0, "per_model": {}}
        try:
            return json.loads(self.state_path.read_text())
        except Exception:
            return {"date": date.today().isoformat(), "total_usd": 0.0, "per_model": {}}

    def _save_state(self) -> None:
        self.state_path.write_text(json.dumps(self._state, indent=2))

    def _reset_if_new_day(self) -> None:
        if self._state.get("date") != date.today().isoformat():
            self._state = {"date": date.today().isoformat(), "total_usd": 0.0, "per_model": {}}
            self._save_state()

    def _load_pricing(self) -> dict[str, Any]:
        p = Path(getattr(self.config, "pricing_file", "")).expanduser()
        if p.exists():
            try:
                return json.loads(p.read_text())
            except Exception:
                pass
        # Conservative default prices (approximate; users should supply pricing_file)
        return {
            "claude-opus-4.7":    {"input_per_million_usd": 15.00, "output_per_million_usd": 75.00},
            "claude-sonnet-4.5":  {"input_per_million_usd":  3.00, "output_per_million_usd": 15.00},
            "claude-haiku-4.6":   {"input_per_million_usd":  1.00, "output_per_million_usd":  5.00},
            "gpt-5.2":            {"input_per_million_usd":  5.00, "output_per_million_usd": 15.00},
            "gpt-5.2-mini":       {"input_per_million_usd":  0.50, "output_per_million_usd":  1.50},
        }
