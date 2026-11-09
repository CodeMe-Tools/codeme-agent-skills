"""Repository Ownership Router and Boundary Verification.

Implements ADR-0004: Repository Ownership Registry & Agent Routing.
Ensures autonomous coding agents direct code only to authorized repositories,
preventing proprietary IP leaks, secret disclosures, and boundary violations.
"""

from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple


@dataclass
class RepositoryEntry:
    name: str
    visibility: str  # "public" or "private"
    license: str
    description: str
    path: str
    allowed_components: List[str]
    ci_required: bool


@dataclass
class RoutingDecision:
    file_path: str
    repository_name: Optional[str]
    relative_path: Optional[str]
    visibility: Optional[str]
    allowed: bool
    violations: List[str] = field(default_factory=list)


# Forbidden patterns in public repositories (IP and Secret Protection)
PUBLIC_LEAK_PATTERNS = [
    (r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----", "Private cryptographic key block detected"),
    (r"4a5c9a7b78912ef0d381cf45bf838aa4d62e3fae5743b177891461db2e8623b9", "Platform root private key material detected"),
    (r"from codeme\.licensing import", "Proprietary licensing import in public repository"),
    (r"import codeme\.licensing", "Proprietary licensing import in public repository"),
    (r"from codeme\.billing import", "Proprietary billing import in public repository"),
    (r"import codeme\.billing", "Proprietary billing import in public repository"),
    (r"POLAR_WEBHOOK_SECRET\s*=\s*['\"][^'\"]+['\"]", "Live MoR credential secret detected"),
    (r"LEMONSQUEEZY_WEBHOOK_SECRET\s*=\s*['\"][^'\"]+['\"]", "Live MoR credential secret detected"),
]


class RepositoryRouter:
    """Routes and validates file operations against repository-registry.json."""

    def __init__(self, registry_path: Optional[str | Path] = None):
        self.registry_path = self._resolve_registry_path(registry_path)
        self.registry_data = self._load_registry()
        self.repositories: Dict[str, RepositoryEntry] = {}
        self._init_repositories()

    def _resolve_registry_path(self, given: Optional[str | Path]) -> Path:
        if given:
            p = Path(given).resolve()
            if p.is_file():
                return p

        # Search upwards for config/repository-registry.json
        curr = Path.cwd().resolve()
        for parent in [curr] + list(curr.parents):
            candidate = parent / "config" / "repository-registry.json"
            if candidate.is_file():
                return candidate

        # Fallback relative to this file
        fallback = Path(__file__).resolve().parents[4] / "config" / "repository-registry.json"
        if fallback.is_file():
            return fallback

        raise FileNotFoundError("Could not locate repository-registry.json in workspace hierarchy.")

    def _load_registry(self) -> Dict[str, Any]:
        with open(self.registry_path, "r", encoding="utf-8") as f:
            return json.load(f)

    def _init_repositories(self) -> None:
        for repo_def in self.registry_data.get("repositories", []):
            entry = RepositoryEntry(
                name=repo_def["name"],
                visibility=repo_def.get("visibility", "private"),
                license=repo_def.get("license", "Proprietary"),
                description=repo_def.get("description", ""),
                path=repo_def.get("path", ""),
                allowed_components=repo_def.get("allowed_components", []),
                ci_required=repo_def.get("ci_required", True),
            )
            self.repositories[entry.name] = entry

    @property
    def workspace_root(self) -> Path:
        return self.registry_path.parent.parent.resolve()

    def find_repository_for_path(self, target_path: str | Path) -> Optional[Tuple[RepositoryEntry, str]]:
        """Resolves which repository owns target_path and returns (entry, relative_subpath)."""
        p = Path(target_path)
        resolved_p = p.resolve() if p.is_absolute() else (self.workspace_root / p).resolve()

        # Check by repo directory prefix
        for entry in self.repositories.values():
            repo_abs = (self.workspace_root / entry.path).resolve()
            try:
                rel = resolved_p.relative_to(repo_abs)
                return entry, str(rel)
            except ValueError:
                continue

        # Check by relative path prefix directly (e.g. repos/codeme-community/...)
        norm_str = str(p).replace("\\", "/")
        for entry in self.repositories.values():
            entry_norm = entry.path.replace("\\", "/")
            if norm_str.startswith(entry_norm + "/") or norm_str == entry_norm:
                rel = norm_str[len(entry_norm):].lstrip("/")
                return entry, rel

        return None

    def route_file(self, file_path: str | Path, content: Optional[str] = None) -> RoutingDecision:
        """Determines repository destination and validates against boundary rules."""
        match = self.find_repository_for_path(file_path)
        if not match:
            return RoutingDecision(
                file_path=str(file_path),
                repository_name=None,
                relative_path=None,
                visibility=None,
                allowed=False,
                violations=[f"Unmapped path: '{file_path}' does not reside in any registered repository."],
            )

        repo_entry, rel_subpath = match
        violations: List[str] = []

        # Read content if not provided and file exists
        if content is None:
            actual_file = Path(file_path)
            if not actual_file.is_absolute():
                actual_file = self.workspace_root / actual_file
            if actual_file.is_file():
                try:
                    content = actual_file.read_text(encoding="utf-8")
                except Exception:
                    content = None

        # If repository is public, perform strict IP and secret leak validation
        if repo_entry.visibility == "public" and content:
            for pattern, desc in PUBLIC_LEAK_PATTERNS:
                if re.search(pattern, content):
                    violations.append(
                        f"Boundary Violation: Public repository '{repo_entry.name}' cannot receive "
                        f"proprietary content or secrets ({desc})."
                    )

        return RoutingDecision(
            file_path=str(file_path),
            repository_name=repo_entry.name,
            relative_path=rel_subpath,
            visibility=repo_entry.visibility,
            allowed=(len(violations) == 0),
            violations=violations,
        )

    def validate_batch(self, file_paths: List[str | Path]) -> Dict[str, Any]:
        """Validates a batch of modified or proposed files for cross-repo boundaries."""
        results: List[RoutingDecision] = []
        repos_touched: Set[str] = set()
        all_violations: List[str] = []

        for fp in file_paths:
            decision = self.route_file(fp)
            results.append(decision)
            if decision.repository_name:
                repos_touched.add(decision.repository_name)
            if not decision.allowed:
                all_violations.extend(decision.violations)

        is_cross_repo = len(repos_touched) > 1

        return {
            "allowed": len(all_violations) == 0,
            "repositories_touched": sorted(list(repos_touched)),
            "is_cross_repo": is_cross_repo,
            "violations": all_violations,
            "decisions": [
                {
                    "file_path": d.file_path,
                    "repository": d.repository_name,
                    "visibility": d.visibility,
                    "allowed": d.allowed,
                    "violations": d.violations,
                }
                for d in results
            ],
        }
