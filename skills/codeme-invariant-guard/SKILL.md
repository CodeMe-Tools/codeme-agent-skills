---
name: codeme-invariant-guard
description: Enforce database migrations, state-machine transitions, and golden-baseline invariants without MCP.
---

# Codeme Invariant Guard Skill

Prevents semantic drift, database corruption, and broken contracts.

## Execution Options (No MCP Required)

### Option A: Via `codeme-skills` CLI
```bash
# Check all invariants
codeme-skills invariant-guard --repo . --class all

# Check specific invariant class
codeme-skills invariant-guard --repo . --class database_guard
codeme-skills invariant-guard --repo . --class golden_state
codeme-skills invariant-guard --repo . --class state_machine

# Promote golden baseline (requires explicit authorization)
codeme-skills invariant-guard --repo . --class golden_state --promote-baseline
```

### Option B: Via Standalone Script
```bash
python3 repos/codeme-agent-skills/skills/codeme-invariant-guard/run.py --repo . --class all
```

## Rules
1. **Database Migration Guard:** Never permits destructive column drops, missing sequence files, or unindexed foreign keys.
2. **Golden-State Snapshots:** Ensures output matches registered golden baselines unless explicitly promoted.
3. **State-Machine Transition Checking:** Enforces deterministic state flows without invalid jumps.
