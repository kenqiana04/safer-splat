# REPORT_REPAIR_ACTIVE_RUNTIME_AUTHORITY_AND_ROUTING_BOUNDARY_V2

## Answer first

D-AUTH-001 is closed: the Coordinator no longer derives alternative-search permission, deadline path guards, navigation-timeliness suppression, or policy routing decisions. Raw deadline, backup, candidate, terminal, and reason facts are passed to `Supervisor.route_transition`; `Supervisor` is the sole routing-policy owner and unchanged `Supervisor.arbitrate` remains the sole action selector.

D-TRANS-001 is closed: all 43 PR #107 rows are loaded and their normative metadata is carried from frozen row → `TransitionRule` → `RoutingDecision`, including action authority, failure mapping, requirements, backup retention/creation, theorem interpretation, and explicit route metadata. The six previously destination-derived fields are copied from row/design metadata; no destination-only inference remains. Exact-one resolution remains 43/43 with typed zero/multiple-match blocks.

## Evidence boundary

The Coordinator remains orchestration-only and reuses the unchanged ActiveRunner/PlantCommit/BackupTokenStore/TerminalRuntime/TraceWriter paths. 120 deterministic CPU tests and 24 bounded synthetic R1 probes pass. D-EXC-001 (stage-exception bypass) and D-ALT-001 (alternative status collapse) remain `OPEN_DEFERRED_TO_R2`; latent risks are not expanded. No full conformance, smoke, ACTIVE rollout, GPU, oracle, official100, or real BYPASS pair was executed.

## Decision

`FINAL_STATUS=PASS_REPAIR_ACTIVE_RUNTIME_AUTHORITY_ROUTING_BOUNDARY_V2`

`FINAL_DECISION=FREEZE_R1_AUTHORITY_ROUTING_REPAIR_AND_ADVANCE_R2`

Only next task: `REPAIR_ACTIVE_RUNTIME_EXCEPTION_AND_UNKNOWN_ROUTING_V2`.
