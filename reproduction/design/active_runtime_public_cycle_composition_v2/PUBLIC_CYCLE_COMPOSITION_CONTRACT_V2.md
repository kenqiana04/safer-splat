
# PUBLIC_CYCLE_COMPOSITION_CONTRACT_V2

`ActiveCycleCoordinator` is the sole future composition root. It owns only
sequencing, typed handoff, context evolution, and calls to frozen modules. It
does **not** own certificate mathematics, candidate generation or synthesis,
selection priority, terminal/deadline policy, dynamics, plant authority, or
scientific evaluation.

`Supervisor.route_transition` is the only future routing authority and
`Supervisor.arbitrate` remains the final action-selection authority.
`PlantCommitAdapter.commit` remains the only plant authority. The coordinator
must execute exactly the stage named by a `RoutingDecision`; it may not invent
a default branch, interpret a deadline, or call a fallback on its own.

The canonical cycle is `CYCLE_BEGIN -> L1 -> P0 -> fresh binding -> C0 ->
L2 -> L3 -> routing/arbitration -> commit -> token update -> trace -> cycle
result`. L1 runs once per cycle and C0 is never used to bypass L1. A terminal
path is route-only, goal-hold is disabled, and an assurance boundary produces
no plant command. Existing ActiveRunner mechanics are reused; token and trace
logic is not copied into the coordinator.

This is a contract and implementation handoff only. It does not authorize
implementation, conformance revalidation, smoke, or an active experiment.
