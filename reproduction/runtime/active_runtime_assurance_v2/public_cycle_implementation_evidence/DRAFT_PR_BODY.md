## Summary

Implements the exact PR #121 public-cycle design with a runtime-owned `ActiveCycleCoordinator`, additive immutable types, and Supervisor-owned executable routing for all 43 PR #107 transition rules.

## Authority preservation

- Coordinator orchestrates only; it does not select actions or interpret deadline policy.
- `Supervisor.route_transition` owns exact-one routing; unchanged `Supervisor.arbitrate` remains the sole final selector.
- Unchanged `PlantCommitAdapter.commit` remains the sole plant authority.
- Unchanged ActiveRunner owns commit, token lifecycle, and trace mechanics.
- BYPASS semantic paths are unchanged; `BYPASS_REVALIDATION_REQUIRED=false`.

## CPU-only evidence

- 43/43 executable transition rules
- 32/32 implementation scenarios
- 110/110 runtime tests
- 0 implementation-model counterexamples
- real ACTIVE/GPU/smoke/oracle/official100/real BYPASS pairs: 0/0/0/0/0/0

## Boundary

This PR does not claim that PR #120 conformance has been repaired and does not authorize smoke or real execution.

`FINAL_STATUS=PASS_ACTIVE_RUNTIME_PUBLIC_CYCLE_COMPOSITION_V2_IMPLEMENTATION`

`FINAL_DECISION=FREEZE_PUBLIC_CYCLE_IMPLEMENTATION_AND_ADVANCE_REVALIDATION_DAG`

Only next task: `REVALIDATE_ACTIVE_RUNTIME_CONTRACT_CONFORMANCE_V2`.
