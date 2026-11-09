"""Tests for PublicRepositoryAuditor: Validates all public repositories for IP protection, license conformance, and zero secrets."""

import pytest
from pathlib import Path
from codeme_agent_skills.auditor import PublicRepositoryAuditor


def test_public_repository_auditor_clean():
    auditor = PublicRepositoryAuditor()
    result = auditor.audit_all_public_repositories()

    assert result.passed is True, f"Public repository audit failed with violations: {result.violations}"
    assert result.total_public_repos >= 5
    assert result.total_files_scanned > 20

    # Ensure all audited public repos passed clean
    for summary in result.repo_summaries:
        assert summary.license_ok is True
        assert summary.governance_ok is True
        assert summary.clean_of_secrets is True
        assert summary.clean_of_proprietary_imports is True
        assert len(summary.violations) == 0


def test_public_repository_auditor_detects_secret_leak(tmp_path):
    auditor = PublicRepositoryAuditor()
    
    # Create a dummy fake public repo with a leaked private key
    fake_repo_dir = tmp_path / "fake-public"
    fake_repo_dir.mkdir()
    (fake_repo_dir / "LICENSE").write_text("Apache License 2.0")
    (fake_repo_dir / "README.md").write_text("# Fake Repo")
    (fake_repo_dir / "CONTRIBUTING.md").write_text("# Contributing")
    (fake_repo_dir / "SECURITY.md").write_text("# Security")
    (fake_repo_dir / "THIRD_PARTY_NOTICES.md").write_text("# Notices")
    (fake_repo_dir / ".github" / "workflows").mkdir(parents=True)
    (fake_repo_dir / ".github" / "workflows" / "ci.yml").write_text("name: CI")

    # Inject secret
    (fake_repo_dir / "config.py").write_text("-----BEGIN RSA PRIVATE KEY-----\nMIIEowIBAAKCAQEA0...")

    from codeme_agent_skills.repository_router import RepositoryEntry
    fake_entry = RepositoryEntry(
        name="fake-public",
        visibility="public",
        license="Apache-2.0",
        description="Fake test repo",
        path=str(fake_repo_dir),
        allowed_components=[],
        ci_required=True,
    )

    summary = auditor._audit_single_public_repo(fake_entry, fake_repo_dir)
    assert summary.clean_of_secrets is False
    assert any("Private cryptographic key block detected" in v for v in summary.violations)
