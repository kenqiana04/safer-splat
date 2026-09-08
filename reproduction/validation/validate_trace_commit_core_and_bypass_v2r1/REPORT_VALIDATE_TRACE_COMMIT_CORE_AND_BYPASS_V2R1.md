# REPORT_VALIDATE_TRACE_COMMIT_CORE_AND_BYPASS_V2R1

## Answer first

Phase A is **BLOCKED at 11/12**. C01-C11 pass, all six lightweight properties pass, the PR #129 tests pass 28/28, and the full current runtime package passes 161/161. C12 exposes one narrow but decisive gap: a trial whose committed action ended as `COMMITTED_TRACE_INCOMPLETE` can subsequently be finalized as an ordinary `FINALIZED` zero-record trace. `TrialTraceLock` and `TrialFinalizationResult` contain no durable field preserving the prior incomplete-execution fact, so the required `EVALUATION_INELIGIBLE` status cannot be established mechanically from the finalized evidence.

Accordingly, Phase B was **not run**. This is `NOT_RUN_BY_CORE_GATE`, not a BYPASS pass or failure. No runtime source was changed, and no real ACTIVE, GPU, smoke, scientific-oracle, official100, or real-BYPASS execution occurred.

## Core result

- C01 normal primary: PASS — one plant commit, token and trace complete, session remains `READY`.
- C02 retained backup: PASS — one additional plant commit and trace record; cursor advances 0 to 1.
- C03 assurance boundary: PASS — zero plant, one no-action trace, no fake executed state.
- C04 plant unresolved: PASS — `PLANT_OUTCOME_UNRESOLVED`, `RECOVERY_REQUIRED`, no retry.
- C05/C06 token failures: PASS — confirmed receipt, post-state, and executed identity remain present; sessions are non-ready.
- C07/C08 TRACE-F02: PASS — primary and retained-backup commit facts remain present, actual token/cursor state is retained, trace is incomplete, and sessions are non-ready.
- C09 no-action trace failure: PASS — zero plant and `NO_ACTION_TRACE_INCOMPLETE`.
- C10 TRACE-F03: PASS — records freeze, no lock publishes before persistence, append/run are rejected.
- C11 retry: PASS — exact same content/hash retry finalizes without a new cycle.
- C12 evaluation gate: FAIL — `ActiveCycleCoordinator.finalize_trial` accepts `EVIDENCE_INCOMPLETE`; successful `TraceWriter.finalize` publishes a zero-record lock and changes the session to `FINALIZED`. Neither returned type carries a durable evaluation-ineligibility marker.

The six lightweight properties pass: no incomplete/unresolved state remains `READY`, boundary has no plant, and confirmed commit facts are preserved in the transaction result. The C12 failure is downstream of those properties: finalization can erase the trial-level eligibility distinction even though the immediate transaction result was correct.

## Evidence and claim boundary

The frozen PR #119 BYPASS protocol identity was read and locked: protocol Git blob `3a4adec6d06b43ec53ca60e3bb9a71a0a10c2e40`, raw Git-blob SHA256 `f0206a54551d9fc93ef6a5e5c6a6dbf71c043c7882d0c34030180ca215161c52`, trial IDs `[10,30,50,70,90]`, order `[50,10,30,70,90]`. It was not executed because Phase A did not reach 12/12. Historical PR #119 results are upstream context only and are not presented as post-PR129 revalidation.

This task does not claim crash/restart durability, physical atomicity, BYPASS preservation after PR #129, full PR #127 reconformance, or scientific performance.

## Decision

`FINAL_STATUS=BLOCKED_CORE_VALIDATION_BY_EVALUATION_ELIGIBILITY_GAP`

`FINAL_DECISION=DO_NOT_RUN_BYPASS_AND_REPAIR_TRIAL_LEVEL_EVALUATION_ELIGIBILITY`

Only next task: `REPAIR_TRACE_COMMIT_EVALUATION_ELIGIBILITY_GATE_V2R1`.
