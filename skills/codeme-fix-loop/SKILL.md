---
name: codeme-fix-loop
description: Deterministic syntax, quality, build, and test repair loop for autonomous coding agents.
---

# Codeme Fix Loop Skill

This skill guides coding agents through deterministic code verification and minimal safe repair without guessing or fabricating passes.

## Execution Sequence

1. **Syntax Check & Repair:**
   ```bash
   codeme-syntax run --repo . --fix
   ```
   Ensures AST validity, bracket balancing, and syntax compliance.

2. **Quality & Architecture Rules:**
   ```bash
   codeme-quality run --repo . --fix
   ```
   Enforces cyclomatic complexity thresholds, file/function size limits, DDD boundaries, and clean imports.

3. **Build & Test Verification:**
   ```bash
   codeme-verify run --repo . --fix
   ```
   Builds project artifacts and executes test suites.

4. **Universal Contract:**
   - On success: exit code `0`, empty stdout/stderr.
   - On failure: inspect stderr diagnostic `CDM-xxx`, address root cause, and re-run.
