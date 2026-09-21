# Certified Recovery Deadline-Aware Routing Completion V1 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add explicit supervisor-owned boundary routing for certified Recovery candidates at WARNING and EXPIRED deadlines while preserving all existing selection and plant authority.

**Architecture:** The future patch adds two transition rows and the corresponding supervisor arbitration/lookup predicates. `ActiveCycleCoordinator` remains orchestration-only; it consumes the resolved `RoutingDecision`. `ActiveRunner`, PlantCommit, backup lifecycle, terminal policy, and certification math remain unchanged.

**Tech Stack:** Python dataclasses/enums already used by the active runtime, the frozen CSV transition table, and deterministic CPU unit tests.

---

### Task 1: Extend the frozen routing authority

**Files:**
- Modify: `reproduction/specification/method_logic_closure_v2/STATE_TRANSITION_TABLE_V2.csv` by an additive, separately reviewed change.
- Modify: `reproduction/runtime/active_runtime_assurance_v2/supervisor.py` only in transition lookup/arbitration support.

- [ ] Add `ARB_RECOVERY_WARNING_BOUNDARY` with exact WARNING/no-valid-backup/certified-Recovery predicates and `commit_allowed=false`.
- [ ] Add `ARB_RECOVERY_EXPIRED_BOUNDARY` with exact EXPIRED/no-valid-backup/certified-Recovery predicates and `commit_allowed=false`.
- [ ] Ensure `ARB_BACKUP_GUARD` is evaluated first when a valid retained backup exists; do not alter its existing rule or reason.
- [ ] Ensure `ARB_NAV` remains OPEN-only and primary/alternative semantics are unchanged.
- [ ] Ensure the two new rows resolve to `ASSURANCE_BOUNDARY` and never construct an action.

### Task 2: Add deterministic regression tests

**Files:**
- Create: `tests/test_certified_recovery_deadline_boundary.py`

- [ ] Test certified Recovery + WARNING + no backup resolves `ARB_RECOVERY_WARNING_BOUNDARY`, no commit, no action, and no plant call.
- [ ] Test certified Recovery + EXPIRED + no backup resolves `ARB_RECOVERY_EXPIRED_BOUNDARY`, no commit, no action, and no post-expiry search.
- [ ] Test both deadline states with a valid retained backup resolve existing `ARB_BACKUP_GUARD`.
- [ ] Test OPEN certified Recovery remains `ARB_NAV`.
- [ ] Test UNKNOWN/FAIL/identity mismatch cannot match either new row.
- [ ] Test ordinary primary/alternative candidates cannot match either new row.

### Task 3: Preserve authority and trace invariants

**Files:**
- Inspect only: `active_cycle.py`, `active_runner.py`, `plant_commit.py`, `backup_token_store.py`, `terminal_runtime.py`, and `trace_writer.py`.

- [ ] Prove the coordinator only consumes `RoutingDecision`.
- [ ] Prove no new row permits `PlantCommitAdapter.commit` or `ActiveRunner.commit_active_decision`.
- [ ] Prove exactly one no-action boundary trace is emitted through the existing boundary path.
- [ ] Prove no token cursor is mutated on the boundary path.

### Task 4: Revalidate before any runtime execution

**Files:**
- Update the task-local validator and conformance evidence in the future implementation task.

- [ ] Run the deadline matrix and all existing active-runtime regressions CPU-only.
- [ ] Run full active contract conformance revalidation.
- [ ] Confirm protected runtime/source diff is limited to the authorized additive change.
- [ ] Only after conformance PASS may a later task consider smoke; this design task authorizes no smoke.
