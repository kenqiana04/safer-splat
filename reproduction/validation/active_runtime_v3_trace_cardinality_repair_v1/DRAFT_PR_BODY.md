# [V3] Repair blocked-cycle trace cardinality

## Scope

This Draft PR diagnoses and repairs the narrowly scoped post-L2 blocked-cycle evidence gap found in the immutable PR #145 trial-73 evidence. It does not resume or mutate the old result root and does not run the scientific analyzer.

Upstream parent: `bf0a0792932c02e243236f1b316a41037c95fc69` (`execute-active-runtime-v3-paired-validation-v1`). Frozen protocol SHA-256: `2de32310c84db49f0b8982e2bb63f15d234732250a5c3ddf859fdb75386439c5`.

## Root cause

The old trial's final public cycle had L2 PASS followed by `L3_DISCOVERY_ADMISSION=WARNING`. The frozen `L2_PASS` rule requires OPEN, so Supervisor exact-one lookup correctly produced `ROUTING_RULE_MISSING` and L3 was not entered. Coordinator `_blocked_result` returned directly and bypassed the existing no-action `ActiveCommitTransaction`, producing 355 observations but only 354 traces.

## Repair

The coordinator now asks Supervisor for a typed non-commit `ROUTING_BLOCK` decision and sends it through the unchanged `ActiveRunner.commit_active_decision` / `ActiveCommitTransaction` no-action path. This yields exactly one `ASSURANCE_BOUNDARY_NO_ACTION` trace, zero plant/token mutation, and no action authority. The transition table, deadline policy, controller, radius, dynamics, map, checkpoint, and scientific protocol are unchanged.

## Evidence

- 189 CPU behavior/V3/repair tests PASS (one superseded upstream blob-lock assertion excluded because the two authorized runtime files necessarily change).
- One new GPU regression only: trial 73, fresh retry3 root; 434 cycles, 434 trace records/locks/lines, 433 plant commits, finalized, no hard blocker, all integrity counters zero, V3 hard radius `0.015 q`, historical `0.025 q` authority false.
- Two pre-GPU task-local infrastructure attempts are retained separately and are not trial evidence.
- Old result root is read-only; old four complete trials are not reused; no analyzer or 85-trial continuation ran.

## Review boundary

This PR is runtime evidence-contract repair only. It makes no efficacy, safety-superiority, progress, NI, real-time, or deployment claim.

## Final decision

`FINAL_STATUS=PASS_ACTIVE_RUNTIME_V3_TRACE_CARDINALITY_REPAIR`

`FINAL_DECISION=READY_TO_REFREEZE_ACTIVE_RUNTIME_V3_PAIRED_EXECUTION_HARNESS`

Only next task: `REFREEZE_ACTIVE_RUNTIME_V3_PAIRED_EXECUTION_HARNESS_AFTER_TRACE_CARDINALITY_REPAIR`
