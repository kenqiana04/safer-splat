# Active Runtime Trace/Commit Atomicity V2R1 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement PR #128’s memory-only software transaction state machine so confirmed execution facts survive token/trace failures and incomplete evidence makes the Active session non-runnable.

**Architecture:** Add immutable transaction/finalization types, place active-only sequencing in `ActiveCommitTransaction`, preserve existing plant/token/trace owners, and make Coordinator consume typed results. Trace finalization freezes records before persistence and publishes the lock only after configured writes succeed; no journal, fsync, restart recovery, physical rollback, or scientific evaluation is introduced.

**Tech Stack:** Python dataclasses/enums, existing Active Runtime V2 modules, unittest CPU fixtures, content-addressed canonical SHA-256 identities.

---

### Task 1: Freeze exact inputs

**Files:**
- Create: `reproduction/runtime/active_runtime_assurance_v2/implementation_evidence/trace_commit_atomicity_v2r1/TRACE_COMMIT_IMPLEMENTATION_V2R1_INPUT_LOCK.json`

- [ ] Verify PR #128 exact head/base, PASS design decision, Option B, no-journal decision, 40/40 validation, and zero design counterexamples.
- [ ] Hash all normative PR #128 artifacts, allowed runtime blobs, protected runtime blobs, PR #127 failure evidence, and PR #119 BYPASS evidence.

### Task 2: Add immutable transaction types

**Files:**
- Modify: `reproduction/runtime/active_runtime_assurance_v2/runtime_types.py`
- Test: `reproduction/runtime/active_runtime_assurance_v2/tests/test_trace_commit_atomicity_v2r1.py`

- [ ] Add `CommitTransactionState`, `PlantOutcome`, `TokenMutationStatus`, `TraceStatus`, `EvidenceStatus`, and `FinalizationStatus` enums.
- [ ] Add frozen `CommitTransactionResult` and `TrialFinalizationResult` dataclasses; retain prior fields and add transaction references to cycle context/result.
- [ ] Extend `TrialSessionStatus` with evidence/finalization states while preserving all existing values.

### Task 3: Implement the active-only transaction state machine

**Files:**
- Create: `reproduction/runtime/active_runtime_assurance_v2/commit_transaction.py`
- Modify: `reproduction/runtime/active_runtime_assurance_v2/active_runner.py`
- Test: `reproduction/runtime/active_runtime_assurance_v2/tests/test_trace_commit_atomicity_v2r1.py`

- [ ] Generate deterministic attempt identities from trial/cycle/snapshot/decision/action/map facts.
- [ ] Implement no-action, not-committed, unresolved-plant, committed-token-incomplete, committed-trace-incomplete, and complete results.
- [ ] Preserve receipt, executed identity, post-state, and actual token status after confirmed commitment; never replay plant or fabricate rollback.
- [ ] Delegate only `commit_active_decision`; keep `commit_bypass` action/plant behavior unchanged.

### Task 4: Make finalization retry-safe

**Files:**
- Modify: `reproduction/runtime/active_runtime_assurance_v2/trace_writer.py`
- Modify: `reproduction/runtime/active_runtime_assurance_v2/active_runner.py`
- Test: `reproduction/runtime/active_runtime_assurance_v2/tests/test_trace_commit_atomicity_v2r1.py`

- [ ] Freeze records and content hash on first finalize attempt, reject later append, persist using a testable helper, then publish `_lock` only after success.
- [ ] Preserve successful `finalize()` compatibility and add a typed ActiveRunner finalization-result boundary.
- [ ] Permit explicit same-content retry; map content mismatch to recovery-required without plant work.

### Task 5: Integrate Coordinator session fail-close

**Files:**
- Modify: `reproduction/runtime/active_runtime_assurance_v2/active_cycle.py`
- Test: `reproduction/runtime/active_runtime_assurance_v2/tests/test_trace_commit_atomicity_v2r1.py`

- [ ] Store `CommitTransactionResult` in cycle context/result and advance normally only for complete committed transactions.
- [ ] Map incomplete evidence to `EVIDENCE_INCOMPLETE`, unresolved plant to `RECOVERY_REQUIRED`, and finalize failure to `FINALIZATION_FAILED`.
- [ ] Allow `run_cycle` only from `READY`; return typed committed facts even when the trace is incomplete.

### Task 6: Execute implementation tests and commit runtime

**Files:**
- Test: `reproduction/runtime/active_runtime_assurance_v2/tests/test_trace_commit_atomicity_v2r1.py`

- [ ] Run at least 24 deterministic contract tests covering PR #128’s plan.
- [ ] Run the current Active Runtime package regressions and applicable R1/R2/PR #127 CPU tests.
- [ ] Verify protected blobs, no journal, no oracle edge, no real execution, and `git diff --check`.
- [ ] Commit `runtime(reproduction): implement trace commit consistency V2R1`.

### Task 7: Freeze source and implementation evidence

**Files:**
- Create all required artifacts under `implementation_evidence/trace_commit_atomicity_v2r1/`.

- [ ] Hash the five changed runtime files and all protected blobs into the source freeze.
- [ ] Generate diff/type/transaction/runner/coordinator/TraceWriter/TRACE-F02/TRACE-F03/token/no-action/BYPASS/no-journal audits.
- [ ] Run the actual implementation model checker and require zero counterexamples.
- [ ] Run the 32-check precheck and require `PASS_TRACE_COMMIT_ATOMICITY_V2R1_IMPLEMENTATION_PRECHECK`.
- [ ] Commit `validation(reproduction): freeze trace commit implementation evidence V2R1`.

### Task 8: Publish bounded implementation handoff

**Files:**
- Create: `DRAFT_PR_BODY.md`, `FINAL_DECISION.json`, `downstream_handoff.json`, and the implementation report.

- [ ] Recheck PR #128 and protected blobs, push the implementation branch, and create one Open Draft PR.
- [ ] Copy only the generated `REPORT*.md` to `C:\Users\zlab\Desktop\REPORT`.
- [ ] Stop with only `VALIDATE_ACTIVE_RUNTIME_TRACE_COMMIT_ATOMICITY_V2R1` authorized; do not run targeted validation, real BYPASS, reconformance, smoke, ACTIVE, GPU, oracle, or official100.

## Self-review

- [ ] All prompt sections map to a task and exact file boundary.
- [ ] No placeholder, journal, fsync contract, physical ACID claim, copied plant/token logic, or scientific outcome field exists.
- [ ] Type and status names match PR #128’s frozen design across runtime, tests, model, precheck, report, and handoff.
