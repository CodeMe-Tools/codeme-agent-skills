---
name: codeme-fix-loop
description: Deterministic syntax, quality, build, and test repair loop for autonomous coding agents without MCP.
---

# Codeme Fix Loop Skill

This skill guides coding agents through deterministic code verification and minimal safe repair across all 4 Codeme engines without guessing or fabricating passes.

## Execution Options (No MCP Required)

### Option A: Via `codeme-skills` CLI
```bash
codeme-skills fix-loop --repo <path-to-repo> [--file <path-to-file>] [--verbose]
```

### Option B: Via Standalone Script
```bash
python3 repos/codeme-agent-skills/skills/codeme-fix-loop/run.py --repo .
```

### Option C: Individual Engine Commands
1. **Syntax Check & Repair:**
   ```bash
   codeme-syntax run --repo . --fix
   ```
2. **Quality & Architecture Rules:**
   ```bash
   codeme-quality run --repo . --fix
   ```
3. **Build & Test Verification:**
   ```bash
   codeme-verify run --repo . --fix
   ```
4. **Invariant Engine:**
   ```bash
   codeme-invariant run --repo . --class all
   ```

## Universal Contract
- On success: exit code `0`, empty stdout/stderr.
- On failure: inspect stderr diagnostic `[CDM-xxx]`, address root cause, and re-run.
