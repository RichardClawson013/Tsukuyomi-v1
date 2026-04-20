"""Knee — reflexive destructive-pattern block.

Pure regex, no LLM. Spec: docs/architecture/03_organs.md §4.4.
"""
from __future__ import annotations
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from tsukuyomi.core.types import CanonicalRequest
from tsukuyomi.observability.logging import get_logger

log = get_logger(__name__)


_DEFAULT_PATTERNS = [
    (r"\brm\s+-[rf]+\s+/(\s|$)", "rm_slash_root"),
    (r"rm\s+-[rf]+\s+~($|/)", "rm_home"),
    (r"rm\s+-[rf]+\s+\*($|\s)", "rm_star"),
    (r"dd\s+if=\S+\s+of=/dev/[sh]d[a-z]", "dd_raw_disk"),
    (r"mkfs\.", "mkfs"),
    (r"\bpush\b[^\n]*(?:--force\b|--force-with-lease\b|\s-f\b)[^\n]*\b(main|master|prod|production|release)\b", "force_push_protected"),
    (r"\bforce\s*push\b[^\n]*\b(main|master|prod|production|release)\b", "force_push_protected_alt"),
    (r"\breset\s+--hard\s+HEAD~\d+", "reset_hard_behind"),
    (r":\s*\(\)\s*\{.*:\s*\|\s*:&.*\}\s*;:", "fork_bomb"),
    (r"curl[^|]*\|\s*(bash|sh|zsh|fish)", "curl_pipe_shell"),
    (r"wget[^|]*\|\s*(bash|sh|zsh|fish)", "wget_pipe_shell"),
    (r"chmod\s+(777|-R\s+777)\s+/", "chmod_root_world"),
    (r"(DROP|TRUNCATE)\s+TABLE\s+\S+(?!\s+WHERE)", "sql_destructive_ddl"),
    (r"DELETE\s+FROM\s+\S+\s*;", "sql_delete_without_where"),
    (r"shutdown\s+(-h\s+)?now", "shutdown_now"),
    (r"reboot\s*$", "reboot"),
    (r"init\s+[06]", "init_halt_reboot"),
    (r"systemctl\s+(stop|disable)\s+(ssh|sshd)", "disable_ssh"),
    (r"ufw\s+disable", "ufw_disable"),
    (r"iptables\s+-F", "iptables_flush"),
    (r">\s*/dev/sd[a-z]", "redirect_to_raw_disk"),
    (r"git\s+clean\s+-[dfx]+", "git_clean_wipe"),
    (r"git\s+push\s+.*--mirror", "git_push_mirror"),
    (r"history\s+-c", "history_clear"),
    (r"crontab\s+-r", "crontab_remove"),
    (r"sudo\s+visudo", "edit_sudoers"),
    (r"\bpasswd\s+root\b", "change_root_pw"),
]


@dataclass
class KneeVerdict:
    permitted: bool
    matched_pattern_id: str | None = None
    raw_match: str | None = None


class Knee:
    def __init__(self, config: Any) -> None:
        self.config = config
        flags = re.IGNORECASE if getattr(config, "case_insensitive", True) else 0
        self.patterns: list[tuple[re.Pattern, str]] = [
            (re.compile(p, flags), pid) for p, pid in _DEFAULT_PATTERNS
        ]
        ref = Path(getattr(config, "blocked_patterns_reference", "")).expanduser()
        if ref.exists():
            try:
                data = json.loads(ref.read_text())
                for entry in data.get("patterns", []):
                    self.patterns.append((re.compile(entry["regex"], flags), entry["id"]))
            except Exception as exc:
                log.warning("knee.patterns_load_failed", path=str(ref), error=str(exc))
                raise
        log.info("knee.initialized", pattern_count=len(self.patterns))

    def check(self, req: CanonicalRequest) -> KneeVerdict:
        """Scan the candidate response + any tool calls for destructive patterns.

        Called BEFORE forwarding and ALSO on every outbound tool call the model
        emits during streaming.
        """
        haystack_parts: list[str] = []
        for m in req.messages:
            if isinstance(m.content, str):
                haystack_parts.append(m.content)
            for tc in m.tool_calls:
                haystack_parts.append(json.dumps(tc))
        haystack = "\n".join(haystack_parts)

        return self.check_text(haystack, req.request_id)

    def check_text(self, text: str, request_id: str | None = None) -> KneeVerdict:
        for pat, pid in self.patterns:
            m = pat.search(text)
            if m:
                log.warning("knee.block",
                            request_id=request_id,
                            matched_pattern_id=pid,
                            match_preview=m.group(0)[:80])
                return KneeVerdict(permitted=False, matched_pattern_id=pid, raw_match=m.group(0))
        log.info("knee.permit", request_id=request_id)
        return KneeVerdict(permitted=True)
