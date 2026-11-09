---
name: codeme-repository-router
description: Validates repository boundaries and prevents proprietary IP leaks into public repositories without MCP.
---

# Codeme Repository Router Skill

Guides autonomous agents to write and commit content only to authorized repositories according to `config/repository-registry.json`.

## Execution Options (No MCP Required)

### Option A: Via `codeme-router` CLI
```bash
# Validate target files
codeme-router repos/codeme-community/src/test.py

# Output machine-readable JSON routing decisions
codeme-router --json repos/codeme-community/src/test.py repos/codeme-core/src/secret.py
```

### Option B: Via `codeme-skills` CLI
```bash
codeme-skills route repos/codeme-community/src/test.py
```

### Option C: Via Standalone Script
```bash
python3 repos/codeme-agent-skills/skills/codeme-repository-router/run.py repos/codeme-community/src/test.py
```

## Boundary Rules
- **Public Repositories:** `codeme-community`, `codeme-oem-sdk`, `codeme-docs`, `codeme-agent-skills`, `codeme-examples`, `.github`.
- **Private Repositories:** `codeme-core`, `codeme-commercial`, `codeme-website`.
- **Strict Prohibition:** Under no circumstances may proprietary licensing algorithms, commercial keys, or private engine extensions be committed or pushed to public repositories.
