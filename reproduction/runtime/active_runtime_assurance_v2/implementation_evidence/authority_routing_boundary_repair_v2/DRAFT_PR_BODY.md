## Summary

Closes exactly R1 of PR #124: D-AUTH-001 (Coordinator policy leak) and D-TRANS-001 (frozen transition metadata carrier gap). The repair is limited to `active_cycle.py`, `runtime_types.py`, and `supervisor.py`, with deterministic CPU tests.

## Authority boundary

`ActiveCycleCoordinator` collects facts, encodes typed events, observes deadlines, invokes `Supervisor.route_transition`, dispatches the named stage, calls unchanged `Supervisor.arbitrate`, and reuses unchanged `ActiveRunner.commit_active_decision`. It no longer computes alternative permission, deadline guards, navigation-timeliness suppression, or policy `RoutingDecision` objects. Repeated-route meta blocking is returned by `Supervisor.routing_guard_block`.

`TransitionRule` and `RoutingDecision` now carry the PR #107 row's requirements, action authority, failure mapping, backup-retention/creation flags, theorem interpretation, and explicit route metadata. Exact-one lookup remains 43 rules/43 IDs with typed missing/ambiguous blocks; route flags are not recomputed from destination.

## Scope and evidence

- 120 CPU tests pass (110 PR122 baseline plus 10 R1 tests); 24 bounded R1 probes pass.
- Forbidden runtime modules, PR #107–#124 contracts, and Supervisor `bypass_decision`/`arbitrate`/`certify_candidate` semantics are unchanged. `BYPASS_REVALIDATION_REQUIRED=false`.
- D-EXC-001 and D-ALT-001 are explicitly `OPEN_DEFERRED_TO_R2`; no R2 logic was changed.
- Real ACTIVE, GPU, smoke, oracle, official100, and real BYPASS pair counts are all zero.

This is targeted R1 implementation evidence, not full conformance or scientific evidence. The only next task is `REPAIR_ACTIVE_RUNTIME_EXCEPTION_AND_UNKNOWN_ROUTING_V2`.

`FINAL_STATUS=PASS_REPAIR_ACTIVE_RUNTIME_AUTHORITY_ROUTING_BOUNDARY_V2`

`FINAL_DECISION=FREEZE_R1_AUTHORITY_ROUTING_REPAIR_AND_ADVANCE_R2`
