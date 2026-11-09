"""Tests for Autonomous Issue-to-PR Workflow Automation."""

import pytest
from pathlib import Path
from codeme_agent_skills.workflow import AutonomousWorkflowRunner, WorkflowTask


def test_autonomous_workflow_issue_to_pr():
    runner = AutonomousWorkflowRunner()

    # Define a safe implementation step in codeme-community
    def dummy_feature(worktree: Path):
        feature_file = worktree / "src" / "codeme" / "syntax" / "feature_flag.py"
        feature_file.write_text('"""Autonomous feature flag module."""\n\nFEATURE_ENABLED: bool = True\n', encoding="utf-8")

    task = WorkflowTask(
        task_id="TASK-101",
        title="Implement syntax engine feature flags",
        description="Adds feature flag constant to syntax engine.",
        target_files=["repos/codeme-community/src/codeme/syntax/feature_flag.py"],
        implementation_fn=dummy_feature,
    )

    result = runner.execute(task)

    assert result.status == "success"
    assert result.target_repository == "codeme-community"
    assert "repository_ownership_resolution" in result.stages_passed
    assert "implementation" in result.stages_passed
    assert "codeme-syntax" in result.stages_passed
    assert "codeme-quality" in result.stages_passed
    assert "codeme-verify" in result.stages_passed
    assert "codeme-invariant" in result.stages_passed
    assert "pull_request_and_verification_evidence" in result.stages_passed

    # Verification evidence assertion
    assert result.verification_evidence is not None
    assert result.verification_evidence["silent_success_contract_met"] is True
    assert "verification_digest" in result.verification_evidence
    assert len(result.verification_evidence["verification_digest"]) == 64  # SHA-256

    # Pull request payload assertion
    pr = result.pull_request_payload
    assert pr is not None
    assert pr["title"] == "feat(codeme-community): Implement syntax engine feature flags"
    assert pr["base"] == "main"
    assert result.verification_evidence["verification_digest"] in pr["body"]


def test_workflow_fails_on_boundary_violation():
    runner = AutonomousWorkflowRunner()

    task = WorkflowTask(
        task_id="TASK-102",
        title="Unauthorized export",
        description="Attempts to write proprietary key into public repository.",
        target_files=["invalid_root/unregistered_file.py"],
    )

    result = runner.execute(task)
    assert result.status == "failed"
    assert result.failure_stage == "repository_ownership_resolution"
    assert len(result.diagnostics) > 0
