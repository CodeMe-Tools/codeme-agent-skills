---
name: codeme-repository-router
description: Validates repository boundaries and prevents proprietary IP leaks into public repositories.
---

# Codeme Repository Router Skill

Guides autonomous agents to write and commit content only to authorized repositories according to `config/repository-registry.json`.

## Boundary Rules
- **Public Repositories:** `codeme-community`, `codeme-oem-sdk`, `codeme-docs`, `codeme-agent-skills`, `codeme-examples`, `.github`.
- **Private Repositories:** `codeme-core`, `codeme-commercial`, `codeme-website`.
- **Strict Prohibition:** Under no circumstances may proprietary licensing algorithms, commercial keys, or private engine extensions be committed or pushed to public repositories.
