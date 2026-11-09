---
name: codeme-release-guard
description: Verifies release criteria, signed SBOM, and platform acceptance gates.
---

# Codeme Release Guard Skill

Ensures all 20 release acceptance criteria are satisfied before binary distribution or public release.

## Mandatory Checks
1. Clean-machine multi-platform tests pass (macOS, Ubuntu, Windows).
2. Universal silent success contract verified across all 5 CLIs.
3. Ed25519 cryptographic licensing verified in offline mode.
4. Air-gapped enterprise certificates tested without internet access.
5. SBOM generated and third-party notices audited.
