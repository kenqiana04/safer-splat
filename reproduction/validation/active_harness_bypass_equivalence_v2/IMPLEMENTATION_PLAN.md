# Active Harness BYPASS Equivalence V2 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Freeze and execute a five-pair deterministic Stonehenge QA proving whether the additive BYPASS harness preserves the reference action, plant state, branch, and termination trace exactly.

**Architecture:** A task-local, source-locked adapter reconstructs only the untouched `run.py` control/plant/termination slice. Each arm runs in a fresh process; REFERENCE executes the normative dynamics directly, while BYPASS supplies the same QP action to `ActiveRunner.commit_bypass`. A serial fail-closed pipeline runs sentinel 50 first, then 10/30/70/90, comparing exact float32 bit patterns after every pair.

**Tech Stack:** Python 3.10, PyTorch 2.1.2 CUDA 11.8, NumPy 1.26.4, Clarabel 0.10.0, unittest, JSON/JSONL/CSV, Git/GitHub CLI.

---

### Task 1: Freeze protocol and source locks

**Files:** Create the protocol, environment lock, trial manifest, input lock, reference conformance audit, QA scripts, validator, and unit tests under `reproduction/validation/active_harness_bypass_equivalence_v2/`.

- [x] Verify PR #116 exact identity and hashes for `run.py`, runtime modules, dynamics, CBF, and Stonehenge assets.
- [x] Run `python -B -m unittest discover -s reproduction/validation/active_harness_bypass_equivalence_v2/tests -v`; 6/6 synthetic QA-tool tests passed.
- [x] Commit with `validation(reproduction): freeze active harness bypass QA protocol V2` before any real trial.
- [x] Generate `BYPASS_EQUIVALENCE_EXECUTION_LOCK.json` containing that commit SHA and every protocol/tool hash.

### Task 2: Execute Q0 and sentinel Q1

**Files:** Generate only task-owned server evidence under `/disk1/zlab/maintenance_records/active_harness_bypass_equivalence_v2`.

- [x] Build a task-owned checkout and link the immutable Stonehenge `outputs` and data roots; preserve the zero-step missing-data-link invocation.
- [x] Run compile/import, source-lock, synthetic comparison, protected-diff, and GPU/environment preflight: 11/11 PASS.
- [x] Run trial 50 REFERENCE then BYPASS in fresh processes; the pair did not reach comparison finalization.
- [x] Stop Q2, preserve evidence, classify the first mismatch, apply the one authorized correction, and preserve the post-correction trace-identity blocker.

### Task 3: Execute Q2 serially

**Files:** Generate paired artifacts and comparisons for trial IDs 10, 30, 70, and 90.

- [x] Do not run Q2 because Q1 remained blocked after the sole authorized correction.
- [x] Stop at 4 real executions; a compliant restart would project 14 and exceed the hard cap of 12.
- [x] Freeze empty comparison outputs and the two-entry mismatch register without scientific outcomes.

### Task 4: Validate and close out

**Files:** Create `validation_result.json`, `review.json`, `FINAL_DECISION.json`, `downstream_handoff.json`, `DRAFT_PR_BODY.md`, and `report/REPORT_VERIFY_ACTIVE_HARNESS_BYPASS_EQUIVALENCE_V2.md`.

- [x] Run the final validator; it returned BLOCKED with 14 passed and 10 failed gates because the sentinel pair and five-trial exact gates are incomplete.
- [x] Recheck protocol evidence, protected diff, no ACTIVE/oracle/official100 execution, and clean task-owned GPU state.
- [x] Freeze the blocked evidence for the final task-local commit, branch push, and specified Draft PR creation.
- [x] Copy only the generated `REPORT*.md` to `C:\Users\zlab\Desktop\REPORT` and stop before the next validation stage.
