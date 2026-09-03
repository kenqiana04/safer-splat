# Active Harness BYPASS Equivalence V2 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Freeze and execute a five-pair deterministic Stonehenge QA proving whether the additive BYPASS harness preserves the reference action, plant state, branch, and termination trace exactly.

**Architecture:** A task-local, source-locked adapter reconstructs only the untouched `run.py` control/plant/termination slice. Each arm runs in a fresh process; REFERENCE executes the normative dynamics directly, while BYPASS supplies the same QP action to `ActiveRunner.commit_bypass`. A serial fail-closed pipeline runs sentinel 50 first, then 10/30/70/90, comparing exact float32 bit patterns after every pair.

**Tech Stack:** Python 3.10, PyTorch 2.1.2 CUDA 11.8, NumPy 1.26.4, Clarabel 0.10.0, unittest, JSON/JSONL/CSV, Git/GitHub CLI.

---

### Task 1: Freeze protocol and source locks

**Files:** Create the protocol, environment lock, trial manifest, input lock, reference conformance audit, QA scripts, validator, and unit tests under `reproduction/validation/active_harness_bypass_equivalence_v2/`.

- [ ] Verify PR #116 exact identity and hashes for `run.py`, runtime modules, dynamics, CBF, and Stonehenge assets.
- [ ] Run `python -B -m unittest discover -s reproduction/validation/active_harness_bypass_equivalence_v2/tests -v`; expect all synthetic QA-tool tests to pass.
- [ ] Commit with `validation(reproduction): freeze active harness bypass QA protocol V2` before any real trial.
- [ ] Generate `BYPASS_EQUIVALENCE_EXECUTION_LOCK.json` containing that commit SHA and every protocol/tool hash.

### Task 2: Execute Q0 and sentinel Q1

**Files:** Generate only task-owned server evidence under `/disk1/zlab/maintenance_records/active_harness_bypass_equivalence_v2`.

- [ ] Build a task-owned checkout from the protocol commit and link only the immutable Stonehenge `outputs` asset root.
- [ ] Run compile/import, source-lock, synthetic comparison, protected-diff, and GPU/environment preflight; expect `PASS_BYPASS_EQUIVALENCE_Q0_PREFLIGHT`.
- [ ] Run trial 50 REFERENCE then BYPASS in fresh processes and compare exact bits immediately.
- [ ] Continue only if sentinel verdict is `PASS`; otherwise preserve evidence and classify the first mismatch.

### Task 3: Execute Q2 serially

**Files:** Generate paired artifacts and comparisons for trial IDs 10, 30, 70, and 90.

- [ ] For each ID in fixed order, run REFERENCE then BYPASS, compare immediately, and stop on the first failure.
- [ ] Keep total real executions at 10 unless the frozen bug-only gate authorizes one sentinel rerun pair.
- [ ] Aggregate `per_step_equivalence.csv`, `per_trial_equivalence.json`, `summary.json`, and the mismatch register without scientific outcomes.

### Task 4: Validate and close out

**Files:** Create `validation_result.json`, `review.json`, `FINAL_DECISION.json`, `downstream_handoff.json`, `DRAFT_PR_BODY.md`, and `report/REPORT_VERIFY_ACTIVE_HARNESS_BYPASS_EQUIVALENCE_V2.md`.

- [ ] Run `python -B validate_active_harness_bypass_equivalence_v2.py`; expect `PASS_ACTIVE_HARNESS_BYPASS_EQUIVALENCE_V2_VALIDATION` only if every frozen exact gate passes.
- [ ] Recheck PR #116 identity, protocol locks, protected diff, no ACTIVE/oracle/official100 execution, and clean task-owned GPU state.
- [ ] Commit evidence with `validation(reproduction): verify active harness bypass equivalence V2`, push the branch, and create the specified Draft PR.
- [ ] Copy only the generated `REPORT*.md` to `C:\Users\zlab\Desktop\REPORT` and stop before the next validation stage.
