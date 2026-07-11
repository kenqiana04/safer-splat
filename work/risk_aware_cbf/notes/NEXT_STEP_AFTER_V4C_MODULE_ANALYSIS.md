# V4-C Module Failure Analysis Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Restore the exact minimal V4-C helper closure and document a bounded module-level failure-analysis and redesign program without running an experiment.

**Architecture:** Preserve the original recovery runner and two exact helper imports byte-for-byte. Derive its contract from existing functions and reports; distinguish observed evidence from proposed future measurements. The selected prototype remains a proposal, not an implementation.

**Tech Stack:** Python 3.10 `safer_splat_official`; Git; static source inspection; Markdown.

---

### Task 1: Restore and verify the helper closure

**Files:**
- Create: `work/risk_aware_cbf/scripts/run_risk_aware_v1_pre_cbf_comparison.py`
- Create: `work/risk_aware_cbf/scripts/run_v4b_corrective_dt_filter.py`

- [x] Restore exactly two helpers using `git restore --source safc-v4c-helper-dependency-closure -- <helper paths>`.
- [x] Verify SHA256 `e846ff625ed52d197844bdb2f56df72ab8e09cb3d94f0b42724520112268176e` and `573c0587e238eb160928a8b5349239fc852af91791877d87f6abe55e0062f862`.
- [x] Run `py_compile`, import-only validation, and `--help` in the original 4090 environment; expected result is zero exit status without a trial.

### Task 2: Write V4-C semantics audit

**Files:**
- Create: `work/risk_aware_cbf/paper_materials/V4C_MODULE_SEMANTICS_AUDIT.md`

- [x] Extract `generate_sequences`, `evaluate_sequences`, `rollout_sequence`, activation, candidate, cost, and fallback semantics from the original runner.
- [x] Document inputs, outputs, triggers, candidate families, complexity terms, and that `h` is not meter clearance.

### Task 3: Write failure and candidate-family audit designs

**Files:**
- Create: `work/risk_aware_cbf/paper_materials/V4C_FAILURE_MODE_ANALYSIS.md`
- Create: `work/risk_aware_cbf/paper_materials/V4C_CANDIDATE_FAMILY_AUDIT_PLAN.md`

- [x] Classify F-V4C-1 through F-V4C-10 with current evidence, required measurement, failure category, redesign direction, bounded future experiment, and claim boundary.
- [x] Define generated, feasible, selected, recovery-success, selected-minimum-h, progress, runtime, redundancy, and unique-success statistics for every family.

### Task 4: Compare redesigns and select a bounded prototype

**Files:**
- Create: `work/risk_aware_cbf/paper_materials/V4C_REDESIGN_CANDIDATE_MATRIX.md`
- Create: `work/risk_aware_cbf/paper_materials/NEXT_V4C_PROTOTYPE_DECISION.md`

- [x] Specify R-V4C-1 through R-V4C-5 with hypothesis, difference, benefit, runtime, interface, risks, minimum prototype, success, failure, and stop criteria.
- [x] Select a primary and mechanism-distinct backup without implementing either; primary may be Hierarchical Candidate Evaluation only if it addresses evaluation cost while preserving deterministic candidates.

### Task 5: Update index and validate scope

**Files:**
- Modify: `REPRODUCIBILITY_MANIFEST.md`
- Modify: `work/risk_aware_cbf/notes/NEXT_STEP_AFTER_V4C_MODULE_ANALYSIS.md`

- [x] List the analysis artifacts in the manifest and explicitly exclude new trials, traces, raw results, images, and binaries.
- [x] Record that one bounded prototype smoke needs separate authorization and that R1 remains paused.
- [x] Run `git diff --check`, verify no diff under `cbf`, `splat`, `ellipsoids`, `dynamics`, or `run.py`, then commit the scoped change.

## Completed Analysis and Next Boundary

The closure, module audit, failure analysis, candidate-family audit plan,
redesign matrix, and prototype decision are complete. R1 remains paused. A
separate authorization is required before one bounded V4-C-only smoke of
R-V4C-1; that future task must use a fixed activated cohort, compact aggregate
instrumentation, the original V4-C comparator, and the documented stop rules.
