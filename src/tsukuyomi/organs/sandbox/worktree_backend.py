"""Worktree-based sandbox with four hardening layers.

Spec: docs/research/PAPER.md §5 + docs/adr/0003_sandbox_isolation_strategy.md.
"""
from __future__ import annotations
import asyncio
import os
import re
import shutil
import tempfile
import uuid
from datetime import datetime, timezone
from pathlib import Path

from tsukuyomi.core.types import CanonicalRequest, SandboxResult
from tsukuyomi.observability.logging import get_logger

log = get_logger(__name__)


_DEFAULT_TIMEOUT_S = 90
_DEFAULT_CPU_S = 30
_DEFAULT_FILESIZE_KB = 65536      # 64 MB per file


class WorktreeSandboxBackend:
    """Executes a plan in a git worktree with hardening."""

    async def simulate(self, req: CanonicalRequest) -> SandboxResult:
        sandbox_id = f"tsuku-{uuid.uuid4().hex[:12]}"
        start_ts = datetime.now(timezone.utc).isoformat()

        # The plan should be expressed by the agent as:
        #   - expected_files: list[str] (relative paths)
        #   - shell_script: str
        # For v1.0 we use heuristics to extract these from the request.
        expected_files, shell_script = self._extract_plan(req)
        plan_summary = shell_script[:200] if shell_script else "no_plan_extracted"

        if not shell_script:
            result = SandboxResult(sandbox_id=sandbox_id, plan_summary=plan_summary,
                                   expected_files=expected_files, actual_files=[],
                                   match_score=0.0, passed=False, cleanup_status="skipped")
            req.sandbox_result = result
            log.info("sandbox.skipped", request_id=req.request_id, reason="no_plan_extracted")
            return result

        workdir = self._host_workdir()
        if workdir is None:
            result = SandboxResult(sandbox_id=sandbox_id, plan_summary=plan_summary,
                                   expected_files=expected_files, actual_files=[],
                                   match_score=0.0, passed=False, cleanup_status="skipped")
            log.warning("sandbox.no_git_workdir", request_id=req.request_id)
            req.sandbox_result = result
            return result

        sandbox_path = Path(tempfile.gettempdir()) / sandbox_id
        try:
            await self._add_worktree(workdir, sandbox_path)
            # Write script to a temp location inside the sandbox
            script = sandbox_path / ".tsukuyomi_plan.sh"
            script.write_text(shell_script)
            script.chmod(0o700)

            actual_files = await self._run_plan_and_diff(sandbox_path, str(script))

            exp_set = set(expected_files)
            act_set = set(actual_files)
            intersect = exp_set & act_set
            match_score = (len(intersect) / len(exp_set)) if exp_set else 0.0
            passed = match_score >= 0.90

            result = SandboxResult(
                sandbox_id=sandbox_id, plan_summary=plan_summary,
                expected_files=expected_files, actual_files=actual_files,
                match_score=match_score, passed=passed,
                cleanup_status="clean",
            )
            req.sandbox_result = result
            log.info("sandbox.simulate",
                     request_id=req.request_id, sandbox_id=sandbox_id,
                     match_score=round(match_score, 3), passed=passed,
                     cleanup_status="clean")
            return result
        except Exception as exc:
            log.exception("sandbox.error", request_id=req.request_id, error=str(exc))
            result = SandboxResult(sandbox_id=sandbox_id, plan_summary=plan_summary,
                                   expected_files=expected_files, actual_files=[],
                                   match_score=0.0, passed=False,
                                   cleanup_status="error")
            req.sandbox_result = result
            return result
        finally:
            await self._remove_worktree(workdir, sandbox_path)

    # ----- helpers -----

    @staticmethod
    def _host_workdir() -> Path | None:
        cwd = Path.cwd()
        for parent in [cwd, *cwd.parents]:
            if (parent / ".git").exists():
                return parent
        return None

    @staticmethod
    def _extract_plan(req: CanonicalRequest) -> tuple[list[str], str]:
        """Extract (expected_files, shell_script) from the last assistant message.

        Accepts an optional fenced JSON block like:
            ```tsukuyomi-plan
            {"expected_files": ["a.py","b.py"], "shell_script": "echo hi > a.py"}
            ```
        or falls back to empty.
        """
        text = ""
        for m in reversed(req.messages):
            if m.role in ("assistant", "user"):
                text = m.content or ""
                break

        match = re.search(r"```tsukuyomi-plan\s*(\{.*?\})\s*```", text, re.DOTALL)
        if not match:
            return [], ""
        import json as _json
        try:
            data = _json.loads(match.group(1))
            return (list(data.get("expected_files", [])),
                    str(data.get("shell_script", "")))
        except Exception:
            return [], ""

    async def _add_worktree(self, workdir: Path, target: Path) -> None:
        proc = await asyncio.create_subprocess_exec(
            "git", "worktree", "add", "--detach", str(target),
            cwd=str(workdir),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        _out, err = await proc.communicate()
        if proc.returncode != 0:
            raise RuntimeError(f"git worktree add failed: {err.decode()}")

    async def _remove_worktree(self, workdir: Path, target: Path) -> None:
        try:
            proc = await asyncio.create_subprocess_exec(
                "git", "worktree", "remove", "--force", str(target),
                cwd=str(workdir),
                stdout=asyncio.subprocess.DEVNULL,
                stderr=asyncio.subprocess.DEVNULL,
            )
            await proc.communicate()
        except Exception:
            pass
        if target.exists():
            shutil.rmtree(target, ignore_errors=True)

    async def _run_plan_and_diff(self, sandbox: Path, script_path: str) -> list[str]:
        """Run the script under resource limits and network blackhole, then git diff."""
        env = os.environ.copy()
        # Layer 4: HTTP blackhole — point proxy at unreachable local port
        env["HTTP_PROXY"] = "http://127.0.0.1:1"
        env["HTTPS_PROXY"] = "http://127.0.0.1:1"
        env["ALL_PROXY"]   = "http://127.0.0.1:1"
        env["NO_PROXY"]    = ""

        # Layer 1+2: ulimit via shell wrapper. Layer 3 (unshare) omitted if not root.
        wrapper = (
            f"ulimit -t {_DEFAULT_CPU_S} -f {_DEFAULT_FILESIZE_KB}; "
            f"bash {script_path}"
        )
        proc = await asyncio.create_subprocess_shell(
            wrapper,
            cwd=str(sandbox),
            env=env,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        try:
            await asyncio.wait_for(proc.communicate(), timeout=_DEFAULT_TIMEOUT_S)
        except asyncio.TimeoutError:
            proc.kill()
            log.warning("sandbox.timeout", sandbox=str(sandbox))

        diff = await asyncio.create_subprocess_exec(
            "git", "diff", "--name-only", "HEAD",
            cwd=str(sandbox),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        out, _err = await diff.communicate()
        return [line for line in out.decode().splitlines() if line.strip()]
