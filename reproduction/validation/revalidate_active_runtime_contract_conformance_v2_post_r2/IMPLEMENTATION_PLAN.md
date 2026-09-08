# Post-R2 Active Runtime Contract Reconformance V2 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Produce fresh, CPU-only, complete-matrix evidence that the PR #126 runtime conforms to the frozen PR #107–#121 Active Runtime contracts without changing runtime source.

**Architecture:** A task-local Python harness imports the real runtime package, constructs deterministic injected backends, and executes isolated public-cycle, routing, lifecycle, fault, and ownership scenarios. A separate evidence builder derives compact CSV/JSON reports from frozen inputs and harness results; a validator then checks every required gate and selects PASS or the mechanically appropriate BLOCK status.

**Tech Stack:** Python 3.12 standard library, unittest/pytest-compatible tests, Git blob/SHA-256 locks, CSV/JSON/Markdown evidence.

---

### Task 1: Freeze upstream and validation inputs

**Files:**
- Create: `reproduction/validation/revalidate_active_runtime_contract_conformance_v2_post_r2/POST_R2_ACTIVE_RECONFORMANCE_INPUT_LOCK.json`
- Create: `reproduction/validation/revalidate_active_runtime_contract_conformance_v2_post_r2/POST_R2_RUNTIME_DIFF_AUDIT_V2.json`
- Create: `reproduction/validation/revalidate_active_runtime_contract_conformance_v2_post_r2/build_post_r2_reconformance_v2.py`

- [ ] Verify PR #126 identity, the PR #125/126 locks, the PR #107 transition CSV, PR #119 BYPASS evidence, and PR #124 registers.
- [ ] Hash the 17 core runtime files and all required frozen artifacts into the input lock.
- [ ] Record a zero runtime/production diff against PR #126.

### Task 2: Freeze the complete independent scenario harness

**Files:**
- Create: `reproduction/validation/revalidate_active_runtime_contract_conformance_v2_post_r2/tests/_support.py`
- Create: `reproduction/validation/revalidate_active_runtime_contract_conformance_v2_post_r2/tests/test_post_r2_reconformance.py`
- Create: `reproduction/validation/revalidate_active_runtime_contract_conformance_v2_post_r2/POST_R2_CONFORMANCE_SCENARIO_MANIFEST_V2.json`
- Create: `reproduction/validation/revalidate_active_runtime_contract_conformance_v2_post_r2/model_check_post_r2_active_runtime_conformance_v2.py`
- Create: `reproduction/validation/revalidate_active_runtime_contract_conformance_v2_post_r2/validate_post_r2_active_runtime_contract_conformance_v2.py`

- [ ] Define fresh fixture factories for normal, FAIL, UNKNOWN, exception, deadline, alternative, backup, terminal, boundary, trace-fault, and BYPASS-preservation domains.
- [ ] Mechanically generate 43 expected transition fixtures from the frozen CSV and assert exact row metadata plus exact-one resolution.
- [ ] Define at least 60 deterministic scenarios, including all 12 genuine E2E cases and the five latent-risk disambiguations.
- [ ] Freeze the model checker and 54-gate validator source before substantive execution.

### Task 3: Freeze execution authority

**Files:**
- Create: `reproduction/validation/revalidate_active_runtime_contract_conformance_v2_post_r2/POST_R2_ACTIVE_RECONFORMANCE_EXECUTION_LOCK.json`

- [ ] Hash the input lock, fixtures, expected transition matrix, scenario manifest, test source, model checker, validator, and builder.
- [ ] Set `CONFORMANCE_SWEEP_MODE=COMPLETE_INDEPENDENT_MATRIX`, `RUNTIME_CORRECTION_QUOTA=0`, and `TEST_EXPECTATION_CORRECTION_QUOTA=0`.
- [ ] Commit the frozen harness without runtime changes.

### Task 4: Execute CPU-only independent matrix

**Files:**
- Create: `reproduction/validation/revalidate_active_runtime_contract_conformance_v2_post_r2/test_results.json`
- Create: `reproduction/validation/revalidate_active_runtime_contract_conformance_v2_post_r2/POST_R2_CONFORMANCE_SCENARIO_RESULTS_V2.json`
- Create: `reproduction/validation/revalidate_active_runtime_contract_conformance_v2_post_r2/POST_R2_CONFORMANCE_FAILURE_REGISTER_V2.csv`

- [ ] Run the PR #126 133-test applicable runtime suite and record exact results.
- [ ] Run the frozen post-R2 test module without fail-fast so all independent cases execute.
- [ ] Run the actual-runtime model checker and enumerate every counterexample.
- [ ] Record failures without changing runtime source or test expectations.

### Task 5: Materialize closure and latent-risk evidence

**Files:**
- Create all required `POST_R2_*.json` and `POST_R2_*.csv` evidence files listed by the protocol.

- [ ] Build the four-defect closure matrix with static, dynamic, and frozen-authority evidence.
- [ ] Build authority-owner, 43-row fidelity, dynamic coverage, canonical order, deadline, alternative, backup, terminal, exception, commit, boundary, trace, BYPASS, numeric, and NOT_A_BUG evidence.
- [ ] Resolve R-BK-001, R-TERM-001, R-UNK-001, R-TRACE-001, and R-BYPASS-001 to a supported verdict.

### Task 6: Validate, review, report, and publish

**Files:**
- Create: `reproduction/validation/revalidate_active_runtime_contract_conformance_v2_post_r2/validation_result.json`
- Create: `reproduction/validation/revalidate_active_runtime_contract_conformance_v2_post_r2/post_r2_active_runtime_contract_conformance_review.json`
- Create: `reproduction/validation/revalidate_active_runtime_contract_conformance_v2_post_r2/FINAL_DECISION.json`
- Create: `reproduction/validation/revalidate_active_runtime_contract_conformance_v2_post_r2/downstream_handoff.json`
- Create: `reproduction/validation/revalidate_active_runtime_contract_conformance_v2_post_r2/DRAFT_PR_BODY.md`
- Create: `reproduction/validation/revalidate_active_runtime_contract_conformance_v2_post_r2/report/REPORT_REVALIDATE_ACTIVE_RUNTIME_CONTRACT_CONFORMANCE_V2_POST_R2.md`

- [ ] Run the validator, `git diff --check`, input/execution-lock rechecks, and runtime-diff audit.
- [ ] Select PASS only if every protocol gate passes; otherwise select the mechanically matching BLOCK status and minimal next task.
- [ ] Commit evidence separately, push the branch, and create one Open Draft PR against PR #126's branch.

## Self-review

- Spec coverage: all Parts A–Z are mapped to Tasks 1–6; the matrix continues after independent failures and never mutates runtime.
- Placeholder scan: no implementation placeholder or outcome-dependent threshold is used.
- Type consistency: all dynamic checks import the current frozen runtime types and public APIs directly.
- Execution boundary: real ACTIVE, GPU, smoke, scientific oracle, official100, and real BYPASS counts remain zero.
