# Formal85 Lock-Path R1 Repair Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Repair the pre-cycle child-runner execution-lock path mismatch and freeze an authorization-consistent Retry1 entry without changing scientific semantics.

**Architecture:** Preserve Attempt0 as immutable evidence, change only the runner's lock binding plus execution-attempt identity fields, and add structural validator checks that resolve the runner, launcher, validator, and on-disk lock to one canonical path. Regenerate the canonical lock only after the repair commit.

**Tech Stack:** Python 3.10, pathlib, ast/importlib, JSON, Git worktrees, task-local CPU validation.

---

### Task 1: Freeze Attempt0 evidence

**Files:**
- Create: `repair_r1/ATTEMPT0_FAILURE_AUTHORITY.json`
- Create: `repair_r1/ATTEMPT0_DIAGNOSIS.md`
- Create: `repair_r1/reproduce_lock_path_mismatch_r1.py`
- Create: `repair_r1/PRE_REPAIR_LOCK_PATH_REPRODUCTION.json`

- [ ] Hash the six compact Attempt0 files and assert trial 66, exit 1, no raw trial, no trace lock, no public cycle, and no PlantCommit.
- [ ] Parse the runner assignment and reproduce `FileNotFoundError` for the wrong basename without importing CUDA or running a trial.
- [ ] Commit the immutable diagnosis before changing the runner.

### Task 2: Apply the minimal binding repair

**Files:**
- Modify: `run_post_repair_v3_bounded_recovery_trial_v1.py`
- Modify: `validate_post_repair_v3_bounded_recovery_paired_validation_v1.py`
- Modify: `launch_post_repair_v3_bounded_recovery_paired_validation_v1.py`
- Modify: `POST_REPAIR_V3_BOUNDED_RECOVERY_PAIRED_VALIDATION_PROTOCOL.json`
- Modify: `monitor_post_repair_v3_bounded_recovery_paired_validation_v1.py`
- Modify: `analyze_post_repair_v3_bounded_recovery_paired_validation_v1.py`
- Create: `repair_r1/test_lock_path_repair_r1.py`
- Create: `repair_r1/SCIENTIFIC_SEMANTICS_EQUIVALENCE_AUDIT.json`

- [ ] Write failing CPU checks for canonical basename, one lock file, structured runner/launcher binding, Retry1 identity, token agreement, and scientific-semantic equivalence.
- [ ] Change exactly the runner lock basename and Retry1 execution-attempt identity fields.
- [ ] Add validator checks and run all 18 CPU requirements to PASS.
- [ ] Commit the repair without generating or launching Retry1.

### Task 3: Freeze Retry1 execution identity

**Files:**
- Modify: `POST_REPAIR_V3_BOUNDED_RECOVERY_PAIRED_EXECUTION_LOCK.json`
- Create: `repair_r1/PRELAUNCH_VALIDATION.json`
- Create: `repair_r1/HARNESS_HASHES.json`
- Create: `repair_r1/REPORT_REPAIR_POST_REPAIR_V3_BOUNDED_RECOVERY_FORMAL85_LOCK_PATH_R1.md`

- [ ] Regenerate the canonical lock with the repair commit, Attempt0 hashes, Retry1 token/root/session, and unchanged scientific contracts.
- [ ] Run `python -m py_compile`, CPU tests, validator, and `git diff --check`.
- [ ] Confirm protected diff zero, Retry1 root/tmux absent, Attempt0 hashes unchanged, and execution counts zero.
- [ ] Commit and push; verify remote/local HEAD equality.
