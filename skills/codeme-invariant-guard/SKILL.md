---
name: codeme-invariant-guard
description: Enforce database migrations, state-machine transitions, and golden-baseline invariants.
---

# Codeme Invariant Guard Skill

Prevents semantic drift, database corruption, and broken contracts.

## Rules
1. **Database Migration Guard:**
   ```bash
   codeme-invariant run --repo . --class database_guard
   ```
   Validates schema changes against migration history. Never permits destructive column drops or unindexed foreign keys.

2. **Golden-State Snapshots:**
   ```bash
   codeme-invariant run --repo . --class golden_state
   ```
   Ensures output matches registered golden baselines.
   Baseline updates require explicit authorization:
   ```bash
   codeme-invariant run --repo . --class golden_state --promote-baseline
   ```

3. **State-Machine Transition Checking:**
   ```bash
   codeme-invariant run --repo . --class state_machine
   ```
   Ensures valid state flow without illegal bypasses.
