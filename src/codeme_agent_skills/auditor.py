"""Public Repository Auditor: Validates that open-source repositories contain zero proprietary code, secrets, or license violations."""

from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

from codeme_agent_skills.repository_router import PUBLIC_LEAK_PATTERNS, RepositoryRouter


@dataclass
class RepoAuditSummary:
    repo_name: str
    visibility: str
    files_scanned: int
    license_ok: bool
    governance_ok: bool
    clean_of_secrets: bool
    clean_of_proprietary_imports: bool
    violations: List[str] = field(default_factory=list)


@dataclass
class PublicRepositoryAuditResult:
    passed: bool
    total_public_repos: int
    total_files_scanned: int
    repo_summaries: List[RepoAuditSummary] = field(default_factory=list)
    violations: List[str] = field(default_factory=list)


FORBIDDEN_FILE_PATTERNS = [
    r"^\.env.*$",
    r"^.*\.pem$",
    r"^.*\.key$",
    r"^id_rsa.*$",
    r"^.*\.p12$",
    r"^\.DS_Store$",
]


class PublicRepositoryAuditor:
    """Audits public repositories against IP leaks, secrets, and governance requirements."""

    def __init__(self, workspace_root: Optional[str | Path] = None):
        self.router = RepositoryRouter()
        self.workspace_root = Path(workspace_root).resolve() if workspace_root else self.router.workspace_root

    def audit_all_public_repositories(self) -> PublicRepositoryAuditResult:
        repo_summaries: List[RepoAuditSummary] = []
        all_violations: List[str] = []
        total_scanned = 0

        for repo_entry in self.router.repositories.values():
            if repo_entry.visibility != "public":
                continue

            repo_dir = (self.workspace_root / repo_entry.path).resolve()
            if not repo_dir.is_dir():
                v = f"Public repository directory missing on disk: {repo_dir}"
                all_violations.append(v)
                continue

            summary = self._audit_single_public_repo(repo_entry, repo_dir)
            repo_summaries.append(summary)
            total_scanned += summary.files_scanned
            all_violations.extend(summary.violations)

        passed = len(all_violations) == 0

        return PublicRepositoryAuditResult(
            passed=passed,
            total_public_repos=len(repo_summaries),
            total_files_scanned=total_scanned,
            repo_summaries=repo_summaries,
            violations=all_violations,
        )

    def _audit_single_public_repo(self, entry: Any, repo_dir: Path) -> RepoAuditSummary:
        violations: List[str] = []
        files_scanned = 0
        license_ok = True
        governance_ok = True
        clean_secrets = True
        clean_imports = True

        # 1. Check LICENSE
        lic_file = repo_dir / "LICENSE"
        if not lic_file.is_file() or lic_file.stat().st_size == 0:
            license_ok = False
            violations.append(f"[{entry.name}] Missing or empty LICENSE file.")
        else:
            lic_content = lic_file.read_text(encoding="utf-8", errors="ignore")
            if "Proprietary" in lic_content or "All Rights Reserved" in lic_content:
                license_ok = False
                violations.append(f"[{entry.name}] LICENSE indicates proprietary rights in public repository.")

        # 2. Check Governance (README, CONTRIBUTING, SECURITY, THIRD_PARTY_NOTICES)
        req_gov = ["README.md", "CONTRIBUTING.md", "SECURITY.md", "THIRD_PARTY_NOTICES.md"]
        for g in req_gov:
            gf = repo_dir / g
            if not gf.is_file():
                governance_ok = False
                violations.append(f"[{entry.name}] Missing governance file: {g}")

        # 3. Check CI Workflow
        ci_dir = repo_dir / ".github" / "workflows"
        if entry.ci_required and (not ci_dir.is_dir() or not any(ci_dir.glob("*.yml"))):
            governance_ok = False
            violations.append(f"[{entry.name}] Missing CI workflows in .github/workflows/")

        # 4. Scan files for forbidden artifacts and content leaks
        for root, dirs, files in os.walk(repo_dir):
            # Ignore .git and build caches
            dirs[:] = [d for d in dirs if d not in (".git", "__pycache__", ".pytest_cache", ".venv", "node_modules", "dist", ".astro")]

            for fname in files:
                fpath = Path(root) / fname
                rel_path = fpath.relative_to(repo_dir)

                # Check forbidden file names
                for forbidden in FORBIDDEN_FILE_PATTERNS:
                    if re.match(forbidden, fname, re.IGNORECASE):
                        violations.append(f"[{entry.name}] Forbidden file artifact checked in: {rel_path}")

                # Check file contents for leaks
                # Only check text files
                if fpath.suffix.lower() in (".py", ".ts", ".js", ".swift", ".json", ".md", ".yml", ".yaml", ".sh", ".toml"):
                    files_scanned += 1
                    try:
                        content = fpath.read_text(encoding="utf-8", errors="ignore")
                    except Exception:
                        continue

                    # Audit against leak patterns
                    for pattern, desc in PUBLIC_LEAK_PATTERNS:
                        if re.search(pattern, content):
                            # Skip if this is the auditor or router itself defining the patterns
                            if fpath.name in ("repository_router.py", "auditor.py", "test_repository_router.py", "test_public_repository_auditor.py"):
                                continue

                            if "import" in desc or "Proprietary" in desc:
                                clean_imports = False
                            else:
                                clean_secrets = False
                            violations.append(f"[{entry.name}] Leak detected in {rel_path}: {desc}")

        return RepoAuditSummary(
            repo_name=entry.name,
            visibility=entry.visibility,
            files_scanned=files_scanned,
            license_ok=license_ok,
            governance_ok=governance_ok,
            clean_of_secrets=clean_secrets,
            clean_of_proprietary_imports=clean_imports,
            violations=violations,
        )
