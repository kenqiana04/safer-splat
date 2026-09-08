## Summary

Runs the fixed minimal validation requested for PR #129 without modifying runtime source. Phase A completes all 12 prescribed scenarios plus six lightweight properties and the existing regression suites.

## Result

- Core scenarios: **11/12 PASS**
- Lightweight properties: **6/6 PASS**
- PR #129 implementation tests: **28/28 PASS**
- Current runtime suite: **161/161 PASS**
- Runtime source diff: **0**
- Phase B: **NOT_RUN_BY_CORE_GATE**

C12 found `CORE_VALIDATION_EVALUATION_ELIGIBILITY_GAP`: after a committed trace-append failure, the session is correctly `EVIDENCE_INCOMPLETE`, but `finalize_trial()` can finalize its empty record set, publish an ordinary lock, and set the session to `FINALIZED`. Neither `TrialTraceLock` nor `TrialFinalizationResult` carries an immutable trial-level ineligibility marker. The required evaluation-ineligible condition is therefore not mechanically preserved.

TRACE-F02 primary and retained-backup handling otherwise pass: confirmed receipt/post-state/executed identity survive, token state is not rolled back, and sessions are non-ready. TRACE-F03 persistence-before-lock and exact same-content retry also pass.

The PR #119 frozen five-pair BYPASS protocol was identity-locked but deliberately not executed because the core gate did not reach 12/12. Historical PR #119 evidence is not reused as fresh post-PR129 evidence.

No real ACTIVE, GPU, smoke, scientific oracle, official100, real BYPASS pair, or full PR #127 reconformance was run.

`FINAL_STATUS=BLOCKED_CORE_VALIDATION_BY_EVALUATION_ELIGIBILITY_GAP`

`FINAL_DECISION=DO_NOT_RUN_BYPASS_AND_REPAIR_TRIAL_LEVEL_EVALUATION_ELIGIBILITY`

Only next task: `REPAIR_TRACE_COMMIT_EVALUATION_ELIGIBILITY_GATE_V2R1`.
