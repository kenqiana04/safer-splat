# Active Runtime V3 post-L2 trace-cardinality diagnosis

## Frozen evidence

- Upstream execution branch/head: `execute-active-runtime-v3-paired-validation-v1` / `bf0a0792932c02e243236f1b316a41037c95fc69`.
- Parent protocol head: `0ef0523050fc8e6c77fe333709477c5a4161d489`.
- Frozen protocol SHA-256: `2de32310c84db49f0b8982e2bb63f15d234732250a5c3ddf859fdb75386439c5`.
- Read-only failing evidence: trial `73`, public cycle index `354` (the 355th completed cycle).
- Pre-repair counts: `completed_cycles=355`, `trace_record_count=354`, `trace_lock_record_count=354`, persisted trace lines `=354`, plant commits `=354`.
- The final observation has `committed=false`, `boundary=true`, and no selected or executed action.

## Exact control-flow reconstruction

Cycle 354 completed L1, C0, and L2 with PASS. Before L3, the coordinator observed `L3_DISCOVERY_ADMISSION`; the frozen monotonic deadline observation was `WARNING`. The frozen `L2_PASS` transition row admits L3 only while the deadline is `OPEN`, so exact-one lookup returned zero matches and the Supervisor emitted the typed block `ROUTING_RULE_MISSING`. L3 was therefore correctly not entered.

The defect occurs after that correct routing result. `ActiveCycleCoordinator._blocked_result` returned an `ActiveCycleResult` directly, marking the public cycle as a boundary, but did not call `ActiveRunner.commit_active_decision`. Consequently the existing `ActiveCommitTransaction` no-action branch never appended its `ASSURANCE_BOUNDARY_NO_ACTION` trace record. The plant correctly remained untouched, but one completed public cycle lacked its required trace outcome.

## Root cause

`POST_L2_TYPED_ROUTING_BLOCK_BYPASSED_EXISTING_NO_ACTION_TRACE_TRANSACTION`

This is a runtime evidence-closure defect, not a controller, certificate, deadline-policy, transition-table, V3 geometry, plant, token, or scientific-protocol defect.

## Frozen interpretation

- `L2_PASS + deadline WARNING` remains a typed unresolved route under the frozen table.
- The repair does not add a transition row and does not allow L3 after the warning.
- A no-action trace record is runtime evidence, not a plant commit and not a certified action.
- The old result root remains immutable and scientifically unusable as a repaired primary cohort.
