
# Supervisor-owned routing authority V2

The future public API is:

```text
Supervisor.route_transition(event, runtime_context) -> RoutingDecision
Supervisor.arbitrate(candidate, l3, backup, terminal, deadline) -> SupervisorDecision
```

`route_transition` performs the exact-one lookup in the frozen 43-rule
transition table and returns the rule id, source/destination phase, stage
admission, search permission, arbitration requirement, failure mapping,
deadline interpretation, backup/terminal flags, commit permission, and reason.
The coordinator cannot implement a competing `if/else` policy. Missing or
ambiguous lookup is a typed UNKNOWN/BLOCK event routed back to Supervisor; it
is never guessed.

`arbitrate` remains the only selector of navigation, backup, terminal, or
assurance-boundary action. L1/L2/L3/certifiers report typed evidence only.
The supervisor owns deadline interpretation and alternative permission;
DeadlineTracker remains observation-only.
