"""Codeme Deterministic Fix Loop Skill.

Implements the standard 4-engine verification and deterministic repair loop:
1. codeme-syntax run --fix
2. codeme-quality run --fix
3. codeme-verify run --fix
4. codeme-invariant run

Operates natively without MCP. Adheres to ADR-0002 silent-success contract.
Supports repository-wide scope and scoped modified files (Section 26 Git Integration).
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional


@dataclass
class StepResult:
    step_name: str
    command: List[str]
    exit_code: int
    stdout: str
    stderr: str
    duration_ms: float
    repaired: bool = False


@dataclass
class FixLoopResult:
    status: str  # "success" or "failure"
    exit_code: int
    steps: List[StepResult] = field(default_factory=list)
    diagnostics: List[str] = field(default_factory=list)
    duration_total_ms: float = 0.0


class FixLoopRunner:
    """Executes the deterministic fix loop across a repository or target files."""

    def __init__(
        self,
        repo_path: Optional[str | Path] = None,
        max_attempts: int = 3,
        verbose: bool = False,
    ):
        self.repo_path = Path(repo_path).resolve() if repo_path else Path.cwd().resolve()
        self.max_attempts = max_attempts
        self.verbose = verbose

    def _resolve_binary(self, name: str) -> str:
        venv_bin = Path(sys.executable).parent / name
        if venv_bin.is_file() and os.access(venv_bin, os.X_OK):
            return str(venv_bin)
        which_path = shutil.which(name)
        if which_path:
            return which_path
        return name

    def _execute_command(self, cmd: List[str]) -> StepResult:
        start = time.perf_counter()
        proc = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            cwd=str(self.repo_path),
        )
        elapsed_ms = (time.perf_counter() - start) * 1000.0

        return StepResult(
            step_name=Path(cmd[0]).name,
            command=cmd,
            exit_code=proc.returncode,
            stdout=proc.stdout,
            stderr=proc.stderr,
            duration_ms=round(elapsed_ms, 2),
            repaired=("--fix" in cmd and proc.returncode == 0),
        )

    def run(
        self,
        target_file: Optional[str] = None,
        target_files: Optional[List[str]] = None,
    ) -> FixLoopResult:
        start_time = time.perf_counter()
        steps: List[StepResult] = []
        diagnostics: List[str] = []

        bin_syntax = self._resolve_binary("codeme-syntax")
        bin_quality = self._resolve_binary("codeme-quality")
        bin_verify = self._resolve_binary("codeme-verify")
        bin_invariant = self._resolve_binary("codeme-invariant")

        files_to_check: List[str] = []
        if target_files:
            files_to_check = target_files
        elif target_file:
            files_to_check = [target_file]

        # 1. Syntax Engine (with --fix)
        if files_to_check:
            for tf in files_to_check:
                syntax_cmd = [bin_syntax, "run", "--fix", "--file", tf]
                syntax_res = self._execute_command(syntax_cmd)
                steps.append(syntax_res)
                if syntax_res.exit_code != 0:
                    diag = syntax_res.stderr.strip() or syntax_res.stdout.strip() or f"Syntax verification failed on {tf}."
                    diagnostics.append(f"[CDM-SYN] {diag}")
                    return FixLoopResult(
                        status="failure",
                        exit_code=syntax_res.exit_code,
                        steps=steps,
                        diagnostics=diagnostics,
                        duration_total_ms=round((time.perf_counter() - start_time) * 1000.0, 2),
                    )
        else:
            syntax_cmd = [bin_syntax, "run", "--fix", "--repo", str(self.repo_path)]
            syntax_res = self._execute_command(syntax_cmd)
            steps.append(syntax_res)
            if syntax_res.exit_code != 0:
                diag = syntax_res.stderr.strip() or syntax_res.stdout.strip() or "Syntax verification failed."
                diagnostics.append(f"[CDM-SYN] {diag}")
                return FixLoopResult(
                    status="failure",
                    exit_code=syntax_res.exit_code,
                    steps=steps,
                    diagnostics=diagnostics,
                    duration_total_ms=round((time.perf_counter() - start_time) * 1000.0, 2),
                )

        # 2. Quality Engine (with --fix)
        if files_to_check:
            for tf in files_to_check:
                quality_cmd = [bin_quality, "run", "--fix", "--file", tf]
                quality_res = self._execute_command(quality_cmd)
                steps.append(quality_res)
                if quality_res.exit_code != 0:
                    diag = quality_res.stderr.strip() or quality_res.stdout.strip() or f"Quality verification failed on {tf}."
                    diagnostics.append(f"[CDM-QLT] {diag}")
                    return FixLoopResult(
                        status="failure",
                        exit_code=quality_res.exit_code,
                        steps=steps,
                        diagnostics=diagnostics,
                        duration_total_ms=round((time.perf_counter() - start_time) * 1000.0, 2),
                    )
        else:
            quality_cmd = [bin_quality, "run", "--fix", "--repo", str(self.repo_path)]
            quality_res = self._execute_command(quality_cmd)
            steps.append(quality_res)
            if quality_res.exit_code != 0:
                diag = quality_res.stderr.strip() or quality_res.stdout.strip() or "Quality verification failed."
                diagnostics.append(f"[CDM-QLT] {diag}")
                return FixLoopResult(
                    status="failure",
                    exit_code=quality_res.exit_code,
                    steps=steps,
                    diagnostics=diagnostics,
                    duration_total_ms=round((time.perf_counter() - start_time) * 1000.0, 2),
                )

        # 3. Verify Engine (builds and targeted tests with --fix)
        verify_cmd = [bin_verify, "run", "--repo", str(self.repo_path), "--fix"]
        verify_res = self._execute_command(verify_cmd)
        steps.append(verify_res)
        if verify_res.exit_code != 0:
            diag = verify_res.stderr.strip() or verify_res.stdout.strip() or "Build or test verification failed."
            diagnostics.append(f"[CDM-VRF] {diag}")
            return FixLoopResult(
                status="failure",
                exit_code=verify_res.exit_code,
                steps=steps,
                diagnostics=diagnostics,
                duration_total_ms=round((time.perf_counter() - start_time) * 1000.0, 2),
            )

        # 4. Invariant Engine (database migrations, golden baseline, state machines)
        invariant_cmd = [bin_invariant, "run", "--repo", str(self.repo_path), "--class", "all"]
        invariant_res = self._execute_command(invariant_cmd)
        steps.append(invariant_res)
        if invariant_res.exit_code != 0:
            diag = invariant_res.stderr.strip() or invariant_res.stdout.strip() or "Invariant verification failed."
            diagnostics.append(f"[CDM-INV] {diag}")
            return FixLoopResult(
                status="failure",
                exit_code=invariant_res.exit_code,
                steps=steps,
                diagnostics=diagnostics,
                duration_total_ms=round((time.perf_counter() - start_time) * 1000.0, 2),
            )

        total_ms = round((time.perf_counter() - start_time) * 1000.0, 2)
        return FixLoopResult(
            status="success",
            exit_code=0,
            steps=steps,
            diagnostics=[],
            duration_total_ms=total_ms,
        )
