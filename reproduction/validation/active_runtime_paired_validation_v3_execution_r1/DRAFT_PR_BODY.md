# [V3] Refreeze paired validation execution harness after trace repair

This Draft PR creates a fresh pre-outcome R1 execution harness from accepted PR #146 (`604981dca96cf924679aaf718b78776d858b55b1`, parent `bf0a0792932c02e243236f1b316a41037c95fc69`). The repaired runtime is the protected execution baseline; the old PR #145 harness and old result root remain read-only historical evidence.

The first real launch verified CPU preflight, validator, map/checkpoint loading, and a zero-cycle GPU preflight, then exposed two deterministic harness bugs before any trial raw directory or scientific outcome existed: the batch child lacked existing-root authorization, and the parent assumed a raw directory existed after early child failure.

This repair adds narrow `--batch-child` authority bound by a one-time token, live parent PID, exact retry1 root, source HEAD, execution lock, branch, protocol, and repaired runtime identity. It also preserves early child stdout/stderr/exit/GPU-release diagnostics under `parent_failures/trial_<id>/`, emits a typed nonzero hard stop, never retries, and never fabricates trial evidence.

- Protocol: PR #144, byte-identical SHA `2de32310c84db49f0b8982e2bb63f15d234732250a5c3ddf859fdb75386439c5`.
- Cohort/order: exact frozen 85 primary trials and frozen execution order; development-exposed 15 excluded.
- Execution: future serial separate-process Active trials, seed 0, max 500 cycles, official environment, GPU 1.
- Old failed root: `/disk1/zlab/v3_execution_records/active_runtime_paired_validation_v3_r1_20260914`, superseded read-only diagnostic evidence; never resumed, imported, analyzed, or reused.
- Fresh retry1 root: `/disk1/zlab/v3_execution_records/active_runtime_paired_validation_v3_r1_retry1_20260915`; absent at repair freeze; first launch refuses a collision; explicit resume is exact-root/lock/source bound.
- V3 authority: `0.015 q` hard radius, zero reserve/rho; historical `0.025 q` remains diagnostic-only with no runtime authority.
- Evidence: one trace per completed public cycle, with legitimate no-action boundary cycles allowed and no plant-commit-equals-cycle assumption.
- Reference V2 evidence is reused for the same 85 pairs; Reference rerun is forbidden.
- Analyzer is frozen but not executed; launcher never invokes it.
- Historical failed attempt: one zero-cycle GPU preflight, zero scientific trials.
- This repair: zero GPU preflight, Active trial, analyzer, Reference rerun, Official100, or Formal outcome.

Expected status: `PASS_R1_BATCH_CHILD_ROOT_AND_EARLY_FAILURE_REPAIR`.
Expected decision: `READY_FOR_MANUAL_ACTIVE_RUNTIME_V3_PAIRED_COLLECTION_R1_RETRY1`.
Only next task: `MANUALLY_START_FROZEN_ACTIVE_RUNTIME_V3_PAIRED_COLLECTION_R1_RETRY1`.
