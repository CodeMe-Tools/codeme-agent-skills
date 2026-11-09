"""Tests for RepositoryRouter and boundary enforcement."""

import pytest
from pathlib import Path
from codeme_agent_skills.repository_router import RepositoryRouter


@pytest.fixture
def router():
    return RepositoryRouter()


def test_public_repository_routing(router):
    decision = router.route_file("repos/codeme-community/src/test.py")
    assert decision.allowed is True
    assert decision.repository_name == "codeme-community"
    assert decision.visibility == "public"
    assert len(decision.violations) == 0


def test_private_repository_routing(router):
    decision = router.route_file("repos/codeme-core/src/secret.py")
    assert decision.allowed is True
    assert decision.repository_name == "codeme-core"
    assert decision.visibility == "private"


def test_unmapped_path_rejected(router):
    decision = router.route_file("unmapped_external_dir/file.py")
    assert decision.allowed is False
    assert decision.repository_name is None
    assert any("does not reside in any registered repository" in v for v in decision.violations)


def test_boundary_leak_proprietary_import_rejected_in_public_repo(router):
    leak_code = "from codeme.licensing import verify_ticket\n\ndef main(): pass"
    decision = router.route_file("repos/codeme-community/src/leak.py", content=leak_code)
    assert decision.allowed is False
    assert any("Boundary Violation" in v for v in decision.violations)
    assert any("Proprietary licensing import" in v for v in decision.violations)


def test_boundary_leak_root_key_rejected_in_public_repo(router):
    leak_content = "KEY = '4a5c9a7b78912ef0d381cf45bf838aa4d62e3fae5743b177891461db2e8623b9'"
    decision = router.route_file("repos/codeme-docs/leak.md", content=leak_content)
    assert decision.allowed is False
    assert any("Platform root private key material detected" in v for v in decision.violations)


def test_batch_validation_and_cross_repo_detection(router):
    batch = [
        "repos/codeme-community/src/a.py",
        "repos/codeme-community/src/b.py",
    ]
    res = router.validate_batch(batch)
    assert res["allowed"] is True
    assert res["is_cross_repo"] is False
    assert res["repositories_touched"] == ["codeme-community"]

    cross_batch = [
        "repos/codeme-community/src/a.py",
        "repos/codeme-core/src/c.py",
    ]
    res_cross = router.validate_batch(cross_batch)
    assert res_cross["allowed"] is True
    assert res_cross["is_cross_repo"] is True
    assert set(res_cross["repositories_touched"]) == {"codeme-community", "codeme-core"}
