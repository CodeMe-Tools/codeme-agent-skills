---
name: codeme-release-guard
description: Verifies release criteria, signed SBOM, and platform acceptance gates without MCP.
---

# Codeme Release Guard Skill

Ensures all release acceptance criteria are satisfied before binary distribution or public release.

## Execution Options (No MCP Required)

### Option A: Via `codeme-skills` CLI
```bash
codeme-skills release-guard --root . [--verbose]
```

### Option B: Via Standalone Script
```bash
python3 repos/codeme-agent-skills/skills/codeme-release-guard/run.py --root .
```

## Mandatory Checks
1. Product Manifest integrity and Ed25519 root verification keys.
2. Repository Registry integrity across all registered repos.
3. Toolchain Manager binary operational status.
4. Third-Party Notices and LICENSE files across all repositories.
