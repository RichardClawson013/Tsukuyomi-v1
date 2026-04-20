"""Canonical types used across the pipeline.

These types form the contract between the interceptor layer and the organ layer.
Organs read and write fields on CanonicalRequest as they execute.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Literal, Optional


class Tier(int, Enum):
    """Risk tier assigned by the Skin organ."""
    ROUTINE = 1
    ELEVATED = 2
    HIGH_RISK = 3


class BlastRisk(str, Enum):
    """Blast-radius rating produced by the Shoulders organ."""
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"
    UNKNOWN = "UNKNOWN"


class BudgetZone(str, Enum):
    """Budget zone produced by the Toe organ."""
    GREEN = "GREEN"
    AMBER = "AMBER"
    RED = "RED"


class Decision(str, Enum):
    PERMIT = "permit"
    BLOCK = "block"
    ESCALATE = "escalate"
    DOWNGRADE = "downgrade"


@dataclass
class Message:
    role: Literal["system", "user", "assistant", "tool"]
    content: str
    name: Optional[str] = None
    tool_calls: list[dict[str, Any]] = field(default_factory=list)
    tool_call_id: Optional[str] = None


@dataclass
class ToolDefinition:
    name: str
    description: str
    parameters_schema: dict[str, Any]


@dataclass
class Credential:
    """Represents authorization on a request.
    Tsukuyomi rewrites this on ingestion (see ADR 0001 §coercion / 02_interceptor §5.2).
    """
    raw_header: str          # what the agent sent
    upstream_key: str        # what Tsukuyomi will send to upstream (from env)
    rewritten: bool


@dataclass
class BlastRadius:
    target_symbol: str
    direct_callers: int
    affected_files: list[str]
    risk: BlastRisk

    @classmethod
    def unknown(cls, target: str) -> "BlastRadius":
        return cls(target_symbol=target, direct_callers=0, affected_files=[], risk=BlastRisk.UNKNOWN)


@dataclass
class GaryVerdict:
    audit_id: str
    rounds: list[dict[str, Any]]
    final_decision: Literal["PASS", "BLOCK", "ESCALATED"]
    audit_cost_usd: float
    audit_latency_seconds: float


@dataclass
class SandboxResult:
    sandbox_id: str
    plan_summary: str
    expected_files: list[str]
    actual_files: list[str]
    match_score: float
    passed: bool
    cleanup_status: Literal["clean", "leaked", "error"]


@dataclass
class CanonicalRequest:
    """The internal representation of any agent → upstream LLM request."""
    request_id: str
    inbound_format: Literal["anthropic", "openai"]
    received_at: datetime

    model_requested: str
    messages: list[Message]
    system_prompt: Optional[str]
    tools: list[ToolDefinition]
    max_tokens: int
    temperature: float
    stream: bool
    credential: Credential

    agent_hint: Optional[str] = None

    # Pipeline state, filled in as organs execute.
    tier: Optional[Tier] = None
    is_code_modifying: bool = False
    has_file_writes: bool = False
    blast_radius: Optional[BlastRadius] = None
    gary_verdict: Optional[GaryVerdict] = None
    sandbox_result: Optional[SandboxResult] = None
    toe_zone: Optional[BudgetZone] = None
    model_used: Optional[str] = None              # may differ from requested due to Toe downgrade
    final_decision: Optional[Decision] = None
    block_reason: Optional[str] = None

    @staticmethod
    def now() -> datetime:
        return datetime.now(timezone.utc)
