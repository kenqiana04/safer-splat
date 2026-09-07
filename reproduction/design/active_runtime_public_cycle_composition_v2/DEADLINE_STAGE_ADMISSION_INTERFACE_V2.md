
# Deadline stage-admission interface V2

`DeadlineTracker` emits observations; it has no routing or action authority.
At cycle start, before proposal/candidate work, before an alternative query,
before new L3 discovery, before terminal evaluation, and before the final
commit guard, the coordinator obtains an observation and passes it unchanged
to `Supervisor.route_transition`.

The only states are `DEADLINE_OPEN`, `DEADLINE_WARNING`,
`DEADLINE_EXPIRED`, and typed `DEADLINE_UNKNOWN`. Warning forbids new
high-cost searches. Expired forbids candidate generation, alternative search,
and backup discovery; only already valid/certified choices may be routed.
An expired state is not an unsafe/collision/controller-failure claim. No
concrete millisecond budget is invented here.
