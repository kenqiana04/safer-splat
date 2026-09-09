## Repair result

The exact `finalization.lock` to `finalization.trace_lock` task-local API repair is committed and the dataclass wiring check passed. Runtime and production source diffs remain zero.

The one authorized serial rerun started trial 10. Startup passed, the frozen map loaded on GPU 1, one certified-terminal action was committed, trace cardinality was exactly 1 cycle / 1 trace / 1 locked record, and finalization was `FINALIZED`. No exception, nonfinite value, selected/executed mismatch, action-bound violation, evidence-incomplete state, recovery-required state, or deadline expiry occurred.

The runner nevertheless returned `INCONCLUSIVE_NO_ACTIVE_COMMIT`: it checks the initialized summary `plant_commit_count` before copying the actual `stack["plant"].commit_count`, which was 1. This is a second task-local ordering/wiring defect, not an Active Runtime defect. Per fail-closed instructions, trials 50 and 90 were not started and no further repair or rerun was attempted.

`FINAL_STATUS=BLOCKED_ACTIVE_RUNTIME_SMOKE_BY_WIRING`

`FINAL_DECISION=PRESERVE_RERUN_EVIDENCE_AND_REPAIR_STALE_COMMIT_COUNT_WIRING_ONLY`

Only next task: `REPAIR_ACTIVE_SMOKE_PLANT_COMMIT_COUNT_ORDERING_V2`.
