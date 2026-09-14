# Implementation Plan — Active Runtime V3 Trace Cardinality Repair

> **For execution:** implement this plan in the isolated repair worktree; do not modify or resume the frozen paired-validation result root.

**Goal:** Repair the single missing no-action trace when a completed public cycle exits through a typed post-L2 routing block.

**Architecture:** Preserve the frozen route/deadline policy. Convert a typed routing block into a no-commit `SupervisorDecision`, then pass it through the existing `ActiveRunner.commit_active_decision` and `ActiveCommitTransaction` no-action path so plant count remains unchanged and trace cardinality becomes one record per completed public cycle.

**Tech stack:** Python dataclasses, unittest/pytest-compatible CPU tests, existing Active Runtime V2/V3 stack, one isolated CUDA regression trial.

---

### Task 1: Freeze diagnosis

**Files:**
- Create: `reproduction/validation/active_runtime_v3_trace_cardinality_repair_v1/DIAGNOSIS.md`
- Create: `reproduction/validation/active_runtime_v3_trace_cardinality_repair_v1/REPAIR_CONTRACT.md`

Record the frozen trial-73 cycle-354 evidence, exact route miss, and missing trace path. State explicitly that controller, transition rows, deadline interpretation, V3 geometry, dynamics, and scientific protocol remain unchanged.

### Task 2: Apply minimal runtime repair

**Files:**
- Modify: `reproduction/runtime/active_runtime_assurance_v2/active_cycle.py`
- Modify: `reproduction/runtime/active_runtime_assurance_v2/supervisor.py`

Add a Supervisor-owned no-commit decision for typed orchestration blocks. Route every completed `_blocked_result` through the existing no-action transaction/trace authority.

### Task 3: Add deterministic CPU regressions

**Files:**
- Create: `reproduction/validation/active_runtime_v3_trace_cardinality_repair_v1/tests/test_trace_cardinality_post_l2.py`

Verify the post-L2 deadline-warning reproduction, no L3 execution, no plant commit, exactly one boundary trace, finalized trace lock cardinality, and preservation of normal commit/boundary paths.

### Task 4: Run bounded validation

Run focused tests, all Active Runtime CPU tests, syntax/diff checks, and protected-source checks. Stop if any shared semantic regression appears.

### Task 5: Run one isolated GPU regression

Run only trial 73 in a fresh result root. Verify complete cycle/trace/lock cardinality, plant count, finalization, integrity counters, V3 `0.015 q` runtime authority, and absence of `0.025 q` runtime authority. Do not run trial 66 unless the single authorized trial is insufficient for diagnosis.

### Task 6: Freeze evidence and open Draft PR

Write the regression report, handoff, PR body, commit only the minimal runtime change plus task-local evidence/tests, push the repair branch, and create a Draft PR against `execute-active-runtime-v3-paired-validation-v1`.
