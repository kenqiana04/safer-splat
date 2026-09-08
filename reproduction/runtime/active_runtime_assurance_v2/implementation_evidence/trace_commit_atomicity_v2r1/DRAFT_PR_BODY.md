## Summary

Implements PR #128's frozen `OPTION_B_SOFTWARE_TRANSACTION_STATE_MACHINE` for same-process trace/commit consistency.

- Preserves confirmed receipt, executed action, post-state, and token facts across TRACE-F02.
- Types plant uncertainty, token incompleteness, trace incompleteness, and no-action trace failure.
- Makes incomplete/recovery/finalization-failed sessions non-ready.
- Freezes trace content before persistence and publishes the lock only after success.
- Supports exact same-content finalization retry; identity drift requires recovery.
- Leaves Supervisor/PlantCommit/BackupTokenStore authorities unchanged.
- Adds no journal and makes no durability, restart, or scientific claim.

## Verification

- Targeted tests: 28/28 PASS
- Runtime package: 161/161 PASS
- Model counterexamples: 0
- Protected runtime blobs: exact
- Real execution counts: all zero

Shared `TraceWriter.finalize` changed, so `BYPASS_REVALIDATION_REQUIRED=true`.

`FINAL_STATUS=PASS_IMPLEMENT_ACTIVE_RUNTIME_TRACE_COMMIT_ATOMICITY_V2R1`

`FINAL_DECISION=FREEZE_TRACE_COMMIT_IMPLEMENTATION_AND_ADVANCE_TARGETED_VALIDATION`

Only next task: `VALIDATE_ACTIVE_RUNTIME_TRACE_COMMIT_ATOMICITY_V2R1`.
