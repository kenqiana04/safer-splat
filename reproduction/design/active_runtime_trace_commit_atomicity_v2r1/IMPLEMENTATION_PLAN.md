# Active Runtime Trace/Commit Consistency V2R1 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Freeze and validate a design-only contract that preserves physical execution facts and fails the runtime session closed when token, trace, or finalization evidence is incomplete.

**Architecture:** Reconstruct the actual PR #127 ordering, compare minimal typed fail-close, an in-memory software transaction state machine, and a durable journal without preselection, then mechanically choose the smallest option that satisfies the frozen smoke evidence boundary. All generated material stays in the task-local design directory; runtime and production source remain byte-identical to PR #127.

**Tech Stack:** Python 3 standard library, JSON/CSV/Markdown artifacts, Git blob/SHA-256 identity locks, deterministic design model checking.

---

### Task 1: Freeze upstream and source identities

**Files:**
- Create: `reproduction/design/active_runtime_trace_commit_atomicity_v2r1/TRACE_COMMIT_DESIGN_V2R1_INPUT_LOCK.json`

- [ ] Verify PR #127 state, title, branch, base, and exact head/base SHAs with `gh pr view 127`.
- [ ] Hash the PR #127 report, failure register, trace-fault evidence, counterexamples, validator, reviewer, and both locks.
- [ ] Record Git blob identities for the six runtime files and frozen PR #107/#112/#114/#115/#119/#121 heads.
- [ ] Confirm the four earlier defects are closed and R-TRACE-001 is the only remaining blocker.

### Task 2: Reconstruct current behavior and failure surface

**Files:**
- Create: `CURRENT_ACTIVE_COMMIT_TRACE_ORDER_V2R1.json`
- Create: `CURRENT_TRACE_FINALIZATION_ORDER_V2R1.json`
- Create: `TRACE_COMMIT_FAILURE_MODEL_V2R1.json`
- Create: `TRACE_FINALIZE_IN_MEMORY_DURABILITY_HAZARD_V2R1.json`

- [ ] Trace `ActiveRunner.commit_active_decision` from plant commit through token mutation and trace append.
- [ ] Trace `ActiveCycleCoordinator.finalize_trial` through `TraceWriter.finalize` and session mutation.
- [ ] Record the `_lock`-before-disk hazard and all F1-F13 failure classes without changing runtime.

### Task 3: Compare and mechanically select the consistency architecture

**Files:**
- Create: `TRACE_COMMIT_ARCHITECTURE_COMPARISON_V2R1.csv`
- Create: `TRACE_COMMIT_ARCHITECTURE_DECISION_V2R1.json`
- Create: `TRACE_COMMIT_IMPLEMENTATION_MODULE_DECISION_V2R1.json`
- Create: `TRACE_COMMIT_SMOKE_DURABILITY_DECISION_V2R1.json`

- [ ] Score options A, B, and C against TRACE-F02, TRACE-F03, crash recovery, plant-outcome uncertainty, session fail-close, complexity, BYPASS impact, and smoke evidence needs.
- [ ] Select the lowest-complexity option that closes all frozen same-process conformance failures and explicitly state excluded crash/durability claims.
- [ ] Freeze whether a journal is required and whether the engineering smoke requires durable restart recovery.

### Task 4: Freeze result, session, token, trace, retry, and authority contracts

**Files:**
- Create: `NO_SILENT_UNTRACED_COMMIT_PROPERTY_V2R1.md`
- Create: `TRACE_COMMIT_CONSISTENCY_PROPERTY_V2R1.md`
- Create: `TRACE_FINALIZATION_RETRY_CONTRACT_V2R1.json`
- Create: `TRACE_COMMIT_AUTHORITY_OWNERSHIP_V2R1.json`
- Create: `TRACE_COMMIT_BYPASS_IMPACT_V2R1.json`
- Create: `TRACE_COMMIT_ORACLE_COMPATIBILITY_V2R1.json`

- [ ] Define `CommitTransactionResult`, evidence states, plant-outcome tri-state, and non-ready session states.
- [ ] Freeze no fake rollback, no automatic replay, token state truthfulness, typed append/finalization failure, and bounded idempotent finalization retry.
- [ ] Preserve Supervisor, plant, token, trace, runner, coordinator, and oracle authority boundaries.
- [ ] Mark incomplete evidence and unresolved plant outcomes evaluation-ineligible.

### Task 5: Freeze the fault matrix, invariants, tests, and implementation manifest

**Files:**
- Create: `TRACE_COMMIT_FAULT_MATRIX_V2R1.csv`
- Create: `TRACE_COMMIT_CONSISTENCY_INVARIANTS_V2R1.json`
- Create: `TRACE_COMMIT_IMPLEMENTATION_TEST_PLAN_V2R1.json`
- Create: `TRACE_COMMIT_DESIGN_SCENARIO_MATRIX_V2R1.csv`
- Create: `TRACE_COMMIT_IMPLEMENTATION_CHANGE_MANIFEST_V2R1.csv`

- [ ] Cover F1-F13 and at least 32 symbolic scenarios with typed terminal states.
- [ ] Freeze TCC-01 through TCC-28 and at least 20 future implementation tests.
- [ ] Identify exact future symbols and files without writing production code.

### Task 6: Freeze design inputs and commit the design

**Files:**
- Create: `TRACE_COMMIT_DESIGN_V2R1_EXECUTION_LOCK.json`
- Create: `model_check_trace_commit_consistency_design_v2r1.py`
- Create: `validate_trace_commit_consistency_design_v2r1.py`

- [ ] Hash the architecture decision, failure model, scenario matrix, invariants, model checker, and validator into the execution lock.
- [ ] Verify `git diff --check` and a zero runtime/production diff.
- [ ] Stage only the task-local design directory and commit `design(reproduction): freeze trace commit consistency V2R1`.

### Task 7: Run design-only validation and freeze results

**Files:**
- Create: `TRACE_COMMIT_DESIGN_MODEL_CHECK_V2R1.json`
- Create: `TRACE_COMMIT_DESIGN_COUNTEREXAMPLES_V2R1.json`
- Create: `validation_result.json`
- Create: `trace_commit_consistency_design_v2r1_review.json`
- Create: `FINAL_DECISION.json`
- Create: `downstream_handoff.json`
- Create: `DRAFT_PR_BODY.md`
- Create: `README.md`
- Create: `report/REPORT_DESIGN_ACTIVE_RUNTIME_TRACE_COMMIT_ATOMICITY_V2R1.md`

- [ ] Run the model checker and require zero counterexamples.
- [ ] Run the validator and require `PASS_TRACE_COMMIT_CONSISTENCY_DESIGN_V2R1_VALIDATION`.
- [ ] Recheck PR #127, execution-lock identity, zero runtime diff, and all-zero real execution counts.
- [ ] Commit `validation(reproduction): verify trace commit consistency design V2R1`.

### Task 8: Publish the bounded design handoff

**Files:**
- Modify only generated task-local report and PR-body artifacts if validation metadata requires final synchronization.

- [ ] Push `design-active-runtime-trace-commit-atomicity-v2r1`.
- [ ] Create one Open Draft PR based on `revalidate-active-runtime-contract-conformance-v2-post-r2`.
- [ ] Copy only the generated `REPORT*.md` to `C:\Users\zlab\Desktop\REPORT`.
- [ ] Stop after authorizing only `IMPLEMENT_ACTIVE_RUNTIME_TRACE_COMMIT_ATOMICITY_V2R1`; do not implement, reconform, smoke, or run real trials.

## Self-review

- [ ] Every prompt section 0-45 maps to a task above or a required artifact.
- [ ] No placeholder, runtime implementation, journal preselection, physical ACID claim, or scientific outcome field exists.
- [ ] Type names and state transitions are consistent across property, matrix, model, validator, report, and handoff.
