# Formal85 Lifecycle-Aware Harness R2 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: execute this plan task-by-task in the current isolated worktree. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Repair the Retry1 child-runtime validation phase mismatch, freeze an authorization-consistent Retry2 harness without changing scientific semantics, then launch exactly once and verify nonzero public-cycle evidence.

**Architecture:** Replace the boolean freeze-validator shim with one explicit phase API covering FREEZE, PRELAUNCH, BATCH_RUNTIME, CHILD_RUNTIME, and POSTCOLLECTION. Launcher, child runner, delegated source/map verification, and analyzer each call the phase they own; Retry2 receives new root/session/token identities while Attempt0 and Retry1 remain immutable.

**Tech Stack:** Python 3, dataclasses/enums, JSON locks, Git, tmux, CUDA process inspection, deterministic CPU integration fixtures.

---

### Task 1: Freeze Retry1 failure authority

**Files:**
- Create: `repair_r2/RETRY1_FAILURE_AUTHORITY.json`
- Create: `repair_r2/LIFECYCLE_VALIDATION_CALLSITE_AUDIT.json`

- [ ] Record exact Retry1 file sizes/SHA256, trial 66, exit 1, absent raw evidence, zero cycles, zero PlantCommit, inactive tmux, and immutable authority.
- [ ] Enumerate every validation/startup callsite from launcher through delegate and postcollection analysis.
- [ ] Commit with `Diagnose formal85 retry1 validator phase mismatch`.

### Task 2: Implement explicit lifecycle validation

**Files:**
- Modify: `validate_post_repair_v3_bounded_recovery_paired_validation_v1.py`
- Modify: `run_post_repair_v3_bounded_recovery_trial_v1.py`
- Modify: `launch_post_repair_v3_bounded_recovery_paired_validation_v1.py`

- [ ] Add `ValidationPhase` and `validate_phase(...)` with explicit root/tmux/marker/child-auth/postcollection expectations.
- [ ] Route launcher preflight to PRELAUNCH and batch entry to BATCH_RUNTIME.
- [ ] Route both runner startup and delegated `verify_source_and_map` to CHILD_RUNTIME.
- [ ] Remove every runtime `require_absent_root=False` compatibility call.
- [ ] Keep import-only behavior free of GPU/trial side effects.

### Task 3: Freeze Retry2 execution identity without scientific drift

**Files:**
- Modify: `POST_REPAIR_V3_BOUNDED_RECOVERY_PAIRED_VALIDATION_PROTOCOL.json`
- Modify: `monitor_post_repair_v3_bounded_recovery_paired_validation_v1.py` only if required by dynamic protocol binding
- Modify: `README.md`
- Create: `repair_r2/SCIENTIFIC_SEMANTICS_EQUIVALENCE_AUDIT.json`

- [ ] Set Retry2 root, tmux, token, and launch-marker identity.
- [ ] Add immutable Attempt0 and Retry1 lineage.
- [ ] Compare all frozen cohort/map/geometry/dynamics/Recovery/Reference/NI/boundary fields against R1 and require zero scientific diffs.

### Task 4: Validate startup chain on CPU

**Files:**
- Create: `repair_r2/test_lifecycle_harness_r2.py`
- Create: `repair_r2/CPU_STATIC_INTEGRATION_RESULTS.json`

- [ ] Exercise the five-phase matrix with temporary roots and mocked tmux/process state.
- [ ] Verify token/hash/parent/source/trial/raw guards and both runtime callsites.
- [ ] Import runner/delegate without starting GPU or a trial.
- [ ] Verify local bindings, map/protocol/lock, Recovery wiring reachability, monitor, analyzer boundary, immutable attempt hashes, scientific equivalence, and protected diff.
- [ ] Commit with `Repair formal85 lifecycle-aware validation R2`.

### Task 5: Regenerate the canonical execution lock

**Files:**
- Modify: `POST_REPAIR_V3_BOUNDED_RECOVERY_PAIRED_EXECUTION_LOCK.json`
- Modify: `freeze_post_repair_v3_bounded_recovery_paired_validation_v1.py`
- Create: `repair_r2/PRELAUNCH_VALIDATION.json`
- Create: `repair_r2/REPORT_REPAIR_AND_START_POST_REPAIR_V3_BOUNDED_RECOVERY_FORMAL85_V1.md`

- [ ] Generate hashes from the clean repair commit and include both failed-attempt authorities.
- [ ] Run py_compile, CPU/static integration, phase-aware PRELAUNCH, `git diff --check`, and protected-diff audit.
- [ ] Commit with `Freeze formal85 retry2 execution authority` and push.
- [ ] Verify clean local HEAD equals remote HEAD.

### Task 6: Launch once and prove stable execution

**Files:**
- Runtime evidence only under the frozen Retry2 result root.

- [ ] Recheck absent root/session, clean/pushed HEAD, GPU1 availability, and PRELAUNCH PASS.
- [ ] Launch once with `EXECUTE_POST_REPAIR_V3_BOUNDED_RECOVERY_PAIRED_VALIDATION_V1_R2`.
- [ ] Poll read-only until trial 66 has at least 20 public cycles with no BATCH_STOP and active tmux, or it completes normally and the batch advances.
- [ ] On a new zero-cycle harness failure, preserve the root and repeat with a new attempt identity; on non-harness runtime/scientific failure, stop without method changes.
- [ ] Leave tmux running and hand off the human-readable percentage monitor command; do not run analyzer.
