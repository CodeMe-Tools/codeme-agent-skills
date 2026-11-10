<div align="center">

<a href="https://github.com/CodeMe-Tools">
  <img src="https://raw.githubusercontent.com/CodeMe-Tools/.github/main/profile/assets/codeme-logo.svg" alt="CodeMe Logo" width="80" height="80" />
</a>

# codeme-agent-skills

[![License: Apache-2.0](https://img.shields.io/badge/License-Apache--2.0-blue.svg?style=flat-square)](LICENSE)
[![Platform](https://img.shields.io/badge/Platform-macOS%20%7C%20Linux%20%7C%20Windows-lightgrey.svg?style=flat-square)](#)
[![Visibility](https://img.shields.io/badge/Visibility-PUBLIC-brightgreen.svg?style=flat-square)](#)
[![Deterministic](https://img.shields.io/badge/Deterministic-Zero--Byte%20Success-0ea5e9.svg?style=flat-square)](#)

> **Native coding agent skills for autonomous code verification, repair, and invariant enforcement**

<p>
  <a href="https://github.com/CodeMe-Tools"><b>CodeMe Ecosystem</b></a> &bull;
  <a href="https://github.com/CodeMe-Tools/codeme-docs"><b>Documentation</b></a> &bull;
  <a href="https://codeme.tools"><b>Official Website</b></a>
</p>

---

</div>

## Overview

`codeme-agent-skills` is a core component of **Codeme** — the autonomous code quality, verification, and invariant platform.

### Key Capabilities
- **Deterministic Local Execution:** Zero-byte stdout/stderr on success (`exit 0`), actionable diagnostics on failure.
- **Cross-Platform:** Native support across macOS, Linux (Ubuntu priority), and Windows.
- **Offline-First:** Runs without cloud dependencies or paid per-call inference.
- **Agent-Ready:** Tailored for seamless integration with autonomous AI coding agents.

```mermaid
graph TD
    A[Codeme CLI / Agent] --> B[codeme-agent-skills]
    B --> C[Deterministic Core]
    C --> D{Verification Gate}
    D -->|Success| E[Exit 0 / Silent]
    D -->|Violation| F[Actionable Diagnostics & Rollback]
```

## Governance & Boundaries
- **Ownership:** `codeme-tools/codeme-agent-skills`
- **Visibility:** `PUBLIC`
- **License:** `Apache-2.0`
- **Allowed Component Namespaces:** `skills.fix_loop`, `skills.invariant_guard`, `skills.repository_router`, `skills.release_guard`

## Security Policy
Please review [SECURITY.md](SECURITY.md) for vulnerability reporting guidelines. Under no circumstances may proprietary code or customer tokens be committed to public repositories.

## Contributing
See [CONTRIBUTING.md](CONTRIBUTING.md) for branch management, conventional commit guidelines, and verification rules.
