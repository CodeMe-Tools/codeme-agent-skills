"""Command Line Interfaces for Codeme Agent Skills, Router, and Workflows."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Optional, Sequence

from codeme_agent_skills.repository_router import RepositoryRouter
from codeme_agent_skills.fix_loop import FixLoopRunner
from codeme_agent_skills.invariant_guard import InvariantGuardRunner
from codeme_agent_skills.release_guard import ReleaseGuardRunner
from codeme_agent_skills.workflow import AutonomousWorkflowRunner, WorkflowTask


def router_main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(prog="codeme-router", description="Codeme Repository Ownership & Boundary Router")
    parser.add_argument("paths", nargs="+", help="File paths to route or validate")
    parser.add_argument("--registry", default=None, help="Path to repository-registry.json")
    parser.add_argument("--json", action="store_true", help="Output results in JSON format")

    args = parser.parse_args(argv)
    try:
        router = RepositoryRouter(args.registry)
        res = router.validate_batch(args.paths)
        if args.json:
            print(json.dumps(res, indent=2))
        else:
            if res["allowed"]:
                # Silent success or brief confirmation
                for d in res["decisions"]:
                    print(f"✓ {d['file_path']} -> {d['repository']} ({d['visibility']})")
            else:
                for v in res["violations"]:
                    sys.stderr.write(f"[CDM-ROUTER-001] {v}\n")
        return 0 if res["allowed"] else 1
    except Exception as e:
        sys.stderr.write(f"[CDM-ROUTER-ERR] Error: {e}\n")
        return 2


def workflow_main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(prog="codeme-workflow", description="Codeme Autonomous Issue-to-PR Workflow Automation")
    parser.add_argument("--task-id", required=True, help="Task identifier")
    parser.add_argument("--title", required=True, help="Task title")
    parser.add_argument("--description", default="", help="Task description")
    parser.add_argument("--files", nargs="+", required=True, help="Target files")
    parser.add_argument("--json", action="store_true", help="Output JSON PR payload")

    args = parser.parse_args(argv)
    runner = AutonomousWorkflowRunner()
    task = WorkflowTask(
        task_id=args.task_id,
        title=args.title,
        description=args.description,
        target_files=args.files,
    )
    result = runner.execute(task)

    if args.json:
        print(json.dumps({
            "task_id": result.task_id,
            "status": result.status,
            "target_repository": result.target_repository,
            "stages_passed": result.stages_passed,
            "pull_request_payload": result.pull_request_payload,
            "verification_evidence": result.verification_evidence,
            "diagnostics": result.diagnostics,
        }, indent=2))
    else:
        if result.status == "success":
            print(f"✓ Workflow succeeded for {task.task_id} in {result.target_repository}")
            print(f"  Verification Digest: {result.verification_evidence['verification_digest']}")
        else:
            sys.stderr.write(f"✗ Workflow failed at stage '{result.failure_stage}'\n")
            for d in result.diagnostics:
                sys.stderr.write(f"  {d}\n")

    return 0 if result.status == "success" else 1


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(prog="codeme-skills", description="Codeme Native Coding Agent Skills Runner")
    sub = parser.add_subparsers(dest="skill", help="Agent skill to execute")

    # fix-loop
    p_fix = sub.add_parser("fix-loop", help="Execute deterministic fix loop across 4 engines")
    p_fix.add_argument("--repo", default=".", help="Repository root")
    p_fix.add_argument("--file", default=None, help="Target file")
    p_fix.add_argument("-v", "--verbose", action="store_true", help="Verbose output")

    # invariant-guard
    p_inv = sub.add_parser("invariant-guard", help="Verify invariants or promote golden baselines")
    p_inv.add_argument("--repo", default=".", help="Repository root")
    p_inv.add_argument("--class", dest="inv_class", default="all", choices=["database_guard", "golden_state", "state_machine", "all"])
    p_inv.add_argument("--promote-baseline", action="store_true", help="Promote golden baseline")
    p_inv.add_argument("-v", "--verbose", action="store_true", help="Verbose output")

    # release-guard
    p_rel = sub.add_parser("release-guard", help="Evaluate release criteria and platform gates")
    p_rel.add_argument("--root", default=".", help="Workspace root")
    p_rel.add_argument("-v", "--verbose", action="store_true", help="Verbose output")

    # route
    p_route = sub.add_parser("route", help="Validate repository routing and boundary rules")
    p_route.add_argument("paths", nargs="+", help="File paths to route")

    args = parser.parse_args(argv)

    if args.skill == "fix-loop":
        runner = FixLoopRunner(repo_path=args.repo, verbose=args.verbose)
        res = runner.run(target_file=args.file)
        if res.exit_code == 0:
            if args.verbose:
                print(f"Fix loop completed in {res.duration_total_ms}ms with status: {res.status}")
            return 0
        for d in res.diagnostics:
            sys.stderr.write(f"{d}\n")
        return res.exit_code

    elif args.skill == "invariant-guard":
        runner = InvariantGuardRunner(repo_path=args.repo, verbose=args.verbose)
        res = runner.run(invariant_class=args.inv_class, promote_baseline=args.promote_baseline)
        if res.exit_code == 0:
            if args.verbose:
                print(f"Invariant guard passed ({res.invariant_class})")
            return 0
        for d in res.diagnostics:
            sys.stderr.write(f"[CDM-INV-ERR] {d}\n")
        return res.exit_code

    elif args.skill == "release-guard":
        runner = ReleaseGuardRunner(workspace_root=args.root, verbose=args.verbose)
        res = runner.evaluate()
        if res.exit_code == 0:
            if args.verbose:
                print(f"Release guard approved ({len(res.checks)} checks passed)")
            return 0
        sys.stderr.write(f"Release guard rejected:\n")
        for c in res.checks:
            mark = "✓" if c.passed else "✗"
            sys.stderr.write(f" {mark} {c.name}: {c.details}\n")
        return res.exit_code

    elif args.skill == "route":
        return router_main(args.paths)

    else:
        parser.print_help()
        return 0


if __name__ == "__main__":
    sys.exit(main())
