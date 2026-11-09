"""Codeme Invariant Guard Skill.

Enforces schema immutability, state-machine transitions, and golden-state baselines.
Operates natively without MCP.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional


@dataclass
class InvariantGuardResult:
    status: str
    exit_code: int
    invariant_class: str
    diagnostics: List[str] = field(default_factory=list)
    promoted: bool = False
    duration_ms: float = 0.0


class InvariantGuardRunner:
    """Executes invariant verifications and golden baseline promotions."""

    def __init__(self, repo_path: Optional[str | Path] = None, verbose: bool = False):
        self.repo_path = Path(repo_path).resolve() if repo_path else Path.cwd().resolve()
        self.verbose = verbose

    def _resolve_binary(self) -> str:
        venv_bin = Path(sys.executable).parent / "codeme-invariant"
        if venv_bin.is_file() and os.access(venv_bin, os.X_OK):
            return str(venv_bin)
        return shutil.which("codeme-invariant") or "codeme-invariant"

    def run(
        self,
        invariant_class: str = "all",
        promote_baseline: bool = False,
    ) -> InvariantGuardResult:
        start = time.perf_counter()
        bin_path = self._resolve_binary()

        cmd = [bin_path, "run", "--repo", str(self.repo_path), "--class", invariant_class]
        if promote_baseline:
            cmd.append("--promote-baseline")
        if self.verbose:
            cmd.append("-v")

        proc = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            cwd=str(self.repo_path),
        )
        duration = round((time.perf_counter() - start) * 1000.0, 2)

        diagnostics: List[str] = []
        if proc.returncode != 0:
            msg = proc.stderr.strip() or proc.stdout.strip() or "Invariant check violation"
            diagnostics.append(msg)

        return InvariantGuardResult(
            status="success" if proc.returncode == 0 else "violation",
            exit_code=proc.returncode,
            invariant_class=invariant_class,
            diagnostics=diagnostics,
            promoted=promote_baseline and proc.returncode == 0,
            duration_ms=duration,
        )
