
# [Draft] Design active runtime public cycle composition V2

This design starts from PR #120 exact head `6c5c59dd083dc83661e56c4ddd3e62fa12497652` and preserves its blocker `BLOCKED_ACTIVE_CONFORMANCE_BY_INTEGRATION_ORCHESTRATION_GAP`. It does not modify PR #120, PR #107–#119, runtime code, controller, map, or scientific evidence.

## Design decision

The missing seam is a runtime-owned `ActiveCycleCoordinator`, not another
safety policy. It exposes `start_trial`, `run_cycle`, and `finalize_trial`,
executes one stage named by `Supervisor.route_transition`, and returns a typed
`ActiveCycleResult`. `Supervisor` owns transition routing and final arbitration;
`PlantCommitAdapter.commit` remains the only plant authority; existing
`ActiveRunner.commit_active_decision` owns commit/token/trace mechanics.

The canonical order is CYCLE_BEGIN -> L1 -> P0 -> fresh binding -> C0 -> L2
-> L3 -> routing/arbitration -> commit -> token update -> trace -> result.
Deadline observations are passed to Supervisor; expired means no new search,
not unsafe. Alternatives are native-existing only, no synthesis, and require
fresh C0/L2/L3 certification. Terminal is route-only and goal-hold is disabled.
An assurance boundary never calls plant.

The 43-rule PR107 table is upgraded from a validation manifest to an exact-one
Supervisor routing lookup. Missing/ambiguous lookup is typed block/unknown, not
a coordinator default. BYPASS semantics are preserved; shared changes require
fresh BYPASS revalidation. The corrected ladder is Design -> Implement ->
Revalidate -> Smoke.

## Scope and evidence

This PR is design and static validation only: runtime implementation, active
execution, GPU, rollout, oracle, performance metrics, and smoke are all zero.
Model checking has zero design counterexamples; the validator covers upstream
identity, authority split, phase order, deadline/backup/terminal/boundary,
trace, scenario/invariant coverage, protected diff, and execution counters.

**FINAL_STATUS:** `PASS_ACTIVE_RUNTIME_PUBLIC_CYCLE_COMPOSITION_V2_DESIGN`

**FINAL_DECISION:** `FREEZE_PUBLIC_CYCLE_COMPOSITION_DESIGN_AND_ADVANCE_IMPLEMENTATION_DAG`

**Only next task:** `IMPLEMENT_ACTIVE_RUNTIME_PUBLIC_CYCLE_COMPOSITION_V2`
