"""Tests for native agent skills execution without MCP."""

import pytest
from pathlib import Path
from codeme_agent_skills.fix_loop import FixLoopRunner
from codeme_agent_skills.invariant_guard import InvariantGuardRunner
from codeme_agent_skills.release_guard import ReleaseGuardRunner


def test_fix_loop_execution_on_clean_community_repo():
    repo = Path("repos/codeme-community").resolve()
    runner = FixLoopRunner(repo_path=repo)
    # Target existing clean file
    res = runner.run(target_file="src/codeme/syntax/__init__.py")
    assert res.exit_code == 0
    assert res.status == "success"
    assert len(res.steps) >= 4


def test_invariant_guard_execution():
    repo = Path("repos/codeme-core").resolve()
    runner = InvariantGuardRunner(repo_path=repo)
    res = runner.run(invariant_class="all")
    assert res.exit_code == 0
    assert res.status == "success"
    assert res.invariant_class == "all"


def test_release_guard_evaluation():
    workspace = Path.cwd().resolve()
    runner = ReleaseGuardRunner(workspace_root=workspace)
    res = runner.evaluate()
    assert res.exit_code == 0
    assert res.status == "approved"
    assert len(res.checks) >= 4
    for check in res.checks:
        assert check.passed is True
