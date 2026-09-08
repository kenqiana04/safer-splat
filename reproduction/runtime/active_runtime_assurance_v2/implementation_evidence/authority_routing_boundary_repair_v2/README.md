# R1 authority/routing boundary repair V2

This task closes only PR #124 defects D-AUTH-001 and D-TRANS-001. The Coordinator now carries runtime facts/events only; Supervisor owns frozen routing interpretation and final arbitration. Frozen PR #107 row metadata is copied through `TransitionRule` into `RoutingDecision` without destination-only inference.

D-EXC-001 and D-ALT-001 remain `OPEN_DEFERRED_TO_R2`. Evidence is CPU/static and synthetic only: no rollout, GPU, smoke, oracle, official100, or real BYPASS pair was run. R1 does not authorize full conformance; the only next task is `REPAIR_ACTIVE_RUNTIME_EXCEPTION_AND_UNKNOWN_ROUTING_V2`.
