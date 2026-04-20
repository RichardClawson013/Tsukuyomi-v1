"""Configuration loader.

Loads `corelaw.json`, validates with pydantic, resolves referenced sub-files,
applies env-var lookups for credentials. See ADR 0007.
"""
from __future__ import annotations
import json
import os
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field, ValidationError


class InterceptorConfig(BaseModel):
    host: str = "127.0.0.1"
    port: int = 9999
    credential_passthrough: bool = False
    require_client_token: bool = False
    client_tokens_env_var: str = "TSUKUYOMI_CLIENT_TOKENS"
    stream_pass_through: bool = True
    max_inbound_size_bytes: int = 10_485_760
    request_timeout_seconds: int = 600


class UpstreamProvider(BaseModel):
    base_url: str
    api_key_env_var: str | None = None
    default_model: str | None = None
    timeout_seconds: int = 300


class UpstreamConfig(BaseModel):
    default: str = "anthropic"
    routing: dict[str, str] = Field(default_factory=dict)
    anthropic: UpstreamProvider | None = None
    openai: UpstreamProvider | None = None
    openrouter: UpstreamProvider | None = None
    ollama_local: UpstreamProvider | None = None


class OrganBaseConfig(BaseModel):
    enabled: bool = True


class SkinConfig(OrganBaseConfig):
    rules_file: str = "config/skin_rules.json"
    classifier_threshold_tier2: float = 0.35
    classifier_threshold_tier3: float = 0.65
    default_tier: int = 2


class EarsConfig(OrganBaseConfig):
    activate_on_tiers: list[int] = [2, 3]
    checks: dict[str, bool] = Field(default_factory=lambda: {
        "pronoun_resolution": True,
        "path_disambiguation": True,
        "verb_object_fit": True,
        "scope_indicators": True,
    })


class ShouldersConfig(OrganBaseConfig):
    mcp_command: list[str] = ["npx", "-y", "gitnexus@latest", "mcp"]
    mcp_startup_timeout_seconds: int = 20
    cache_tools_list: bool = True
    thresholds: dict[str, int] = Field(default_factory=lambda: {
        "low_max_callers": 0,
        "medium_max_callers": 5,
        "high_max_callers": 15,
    })
    unknown_treated_as: str = "HIGH"


class KneeConfig(OrganBaseConfig):
    blocked_patterns_reference: str = "config/knee_patterns.json"
    case_insensitive: bool = True
    emergency_override_requires: str = "human_signature"


class ToeConfig(OrganBaseConfig):
    daily_budget_usd: float = 2.00
    warning_threshold_usd: float = 1.50
    state_file: str = "data/budget_state.json"
    pricing_file: str = "config/model_pricing.json"
    downgrade_map: dict[str, str] = Field(default_factory=dict)
    reset_on: str = "midnight_utc"


class EyesConfig(OrganBaseConfig):
    verify_git_diff: bool = True
    verify_content_hash_for_non_git: bool = True
    warn_on_mismatch: bool = True
    block_on_repeated_mismatch: bool = True
    mismatch_threshold_per_session: int = 3


class NoseConfig(OrganBaseConfig):
    window_seconds: int = 60
    max_identical_commands: int = 3
    max_token_rate_per_min: int = 500
    max_tool_calls_per_min: int = 20
    max_errors_per_2min: int = 5
    max_file_changes_per_min_tier12: int = 10
    budget_depletion_alert_fraction_per_hour: float = 0.5


class MouthConfig(OrganBaseConfig):
    interface: str = "cli"
    timeout_seconds: int = 120
    default_on_timeout: str = "deny"
    webhook_url: str | None = None
    webhook_secret_env_var: str = "TSUKUYOMI_MOUTH_WEBHOOK_SECRET"
    approval_triggers: dict[str, Any] = Field(default_factory=dict)


class OrgansConfig(BaseModel):
    skin: SkinConfig = Field(default_factory=SkinConfig)
    ears: EarsConfig = Field(default_factory=EarsConfig)
    shoulders: ShouldersConfig = Field(default_factory=ShouldersConfig)
    knee: KneeConfig = Field(default_factory=KneeConfig)
    toe: ToeConfig = Field(default_factory=ToeConfig)
    eyes: EyesConfig = Field(default_factory=EyesConfig)
    nose: NoseConfig = Field(default_factory=NoseConfig)
    mouth: MouthConfig = Field(default_factory=MouthConfig)


class GaryConfig(BaseModel):
    enabled: bool = True
    activate_on_tier: list[int] = [3]
    activate_on_risk: list[str] = ["HIGH", "CRITICAL"]
    activate_on_irreversible_keywords: list[str] = Field(default_factory=lambda: [
        "drop table", "force push", "reset --hard", "rm -rf", "truncate"
    ])
    activate_on_multi_step_plan: bool = True
    multi_step_threshold: int = 2
    min_answer_lengths: dict[str, int] = Field(default_factory=lambda: {
        "Q1": 150, "Q2": 60, "Q3": 100, "Q4": 100, "Q5": 50
    })
    min_risk_keywords_total: int = 4
    evasion_phrases_file: str = "config/gary_evasion_phrases.json"
    risk_keywords_file: str = "config/gary_risk_keywords.json"
    max_rounds: int = 2
    escalate_to_mouth_on_final_fail: bool = True
    audit_log_dir: str = "data/audits"
    max_cost_per_audit_usd: float = 0.10
    primary_audit_endpoint: str = "same_as_request"
    fallback_audit_endpoint: str = "openrouter/anthropic/claude-haiku-4.6"


class NightShiftConfig(BaseModel):
    enabled: bool = True
    lookback_hours: int = 24
    min_block_count_for_proposal: int = 3
    proposals_dir: str = "data/proposals"
    heuristics_enabled: list[str] = Field(default_factory=lambda: [
        "frequently_blocked_commands",
        "audit_evasion_patterns",
        "skin_classification_drift",
        "budget_calibration",
        "nose_threshold_calibration",
        "untriggered_sandbox_mismatches",
        "gitnexus_staleness",
    ])
    auto_apply: bool = False
    proposal_retention_days: int = 180


class ProtocolsConfig(BaseModel):
    gary: GaryConfig = Field(default_factory=GaryConfig)
    nightshift: NightShiftConfig = Field(default_factory=NightShiftConfig)


class MemoryConfig(BaseModel):
    backend: str = "sqlite_fts5"
    sqlite_path: str = "data/memory.db"
    wal_mode: bool = True
    retention_days_events: int = 365
    retention_days_audits: int = 365
    retention_days_proposals_rejected: int = 180
    retain_message_bodies: bool = False
    retain_tool_call_args: bool = False
    encrypt_bodies_at_rest: bool = True


class ObservabilityConfig(BaseModel):
    log_level: str = "info"
    log_dir: str = "data/logs"
    log_rotation: str = "daily"
    log_retention_days: int = 365
    metrics_enabled: bool = False
    metrics_port: int = 9100
    metrics_path: str = "/metrics"
    tracing_enabled: bool = False
    tracing_sampling: dict[str, float] = Field(default_factory=lambda: {
        "tier_1": 0.01, "tier_2": 0.1, "tier_3": 1.0
    })


class Config(BaseModel):
    schema_version: int = 1
    version_label: str = "1.0.0"
    interceptor: InterceptorConfig = Field(default_factory=InterceptorConfig)
    upstream: UpstreamConfig = Field(default_factory=UpstreamConfig)
    organs: OrgansConfig = Field(default_factory=OrgansConfig)
    protocols: ProtocolsConfig = Field(default_factory=ProtocolsConfig)
    memory: MemoryConfig = Field(default_factory=MemoryConfig)
    observability: ObservabilityConfig = Field(default_factory=ObservabilityConfig)


def load_config(path: str | Path) -> Config:
    """Load a corelaw.json file and validate it.

    Raises ValueError with a clear message if validation fails. This is
    deliberately fail-loud at startup (ADR 0007).
    """
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"Config file not found: {path}")
    try:
        raw = json.loads(path.read_text())
    except json.JSONDecodeError as exc:
        raise ValueError(f"{path}: invalid JSON: {exc}") from exc

    # Resolve `extends` (single level)
    if "extends" in raw:
        parent_path = path.parent / raw.pop("extends")
        parent = json.loads(parent_path.read_text())
        merged = _deep_merge(parent, raw)
        raw = merged

    try:
        return Config.model_validate(raw)
    except ValidationError as exc:
        raise ValueError(f"{path}: config validation failed:\n{exc}") from exc


def _deep_merge(base: dict, override: dict) -> dict:
    out = dict(base)
    for k, v in override.items():
        if k in out and isinstance(out[k], dict) and isinstance(v, dict):
            out[k] = _deep_merge(out[k], v)
        else:
            out[k] = v
    return out
