"""Eyes — post-action verification.

Spec: docs/architecture/03_organs.md §4.6.
"""
from __future__ import annotations
import asyncio
import hashlib
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from tsukuyomi.observability.logging import get_logger

log = get_logger(__name__)


@dataclass
class VerificationResult:
    match: bool
    expected_files: list[str]
    actual_files: list[str]
    surprise_files: list[str]
    missing_files: list[str]


class Eyes:
    def __init__(self, config: Any) -> None:
        self.config = config
        self._session_mismatches: int = 0

    async def verify(self, workdir: Path, expected_files: list[str]) -> VerificationResult:
        workdir = Path(workdir).expanduser()
        actual = await self._git_diff_namelist(workdir)
        if actual is None:
            # Non-git fallback: hash-based comparison is not feasible without a prior snapshot
            actual = []

        exp_set = set(expected_files)
        act_set = set(actual)
        surprise = sorted(act_set - exp_set)
        missing = sorted(exp_set - act_set)
        match = not surprise and not missing

        if not match:
            self._session_mismatches += 1

        log.info("eyes.verify",
                 match_or_mismatch=("match" if match else "mismatch"),
                 expected_count=len(expected_files),
                 actual_count=len(actual),
                 surprise_files_count=len(surprise))
        return VerificationResult(match=match, expected_files=expected_files,
                                  actual_files=actual, surprise_files=surprise,
                                  missing_files=missing)

    @property
    def session_mismatches(self) -> int:
        return self._session_mismatches

    @staticmethod
    async def _git_diff_namelist(workdir: Path) -> list[str] | None:
        if not (workdir / ".git").exists() and not (workdir.parent / ".git").exists():
            return None
        proc = await asyncio.create_subprocess_exec(
            "git", "diff", "--name-only", "HEAD",
            cwd=str(workdir),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        out, _err = await proc.communicate()
        if proc.returncode != 0:
            return None
        return [line for line in out.decode().splitlines() if line.strip()]

    @staticmethod
    def _hash_file(path: Path) -> str:
        if not path.exists():
            return ""
        h = hashlib.sha256()
        h.update(path.read_bytes())
        return h.hexdigest()
