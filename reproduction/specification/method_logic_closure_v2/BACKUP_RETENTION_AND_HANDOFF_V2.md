# Backup retention and handoff V2

`retained_backup_status ∈ {NONE, VALID, INVALID, EXHAUSTED}` is supervisor state, not an incidental certifier result.

A token contains witness ID, source candidate ID, certification cycle, expected state/time index, remaining control tail, map authority ID, geometry contract ID, actuator contract ID, dynamics/timebase ID, terminal target ID, validity predicate, and expiry/consumption state.

`BACKUP_STILL_VALID(x_k, context_k, token)` requires the expected time index, exact frozen-model predicted state, unchanged immutable map authority, identical geometry/actuator/dynamics/timebase identities, a nonempty tail, and no invalidating event. Because tracking error, disturbance, and actuation delay are outside the present theorem, exact state matching is meaningful only under the frozen no-error assumptions.

The old token remains available while primary or alternative evidence is pending. Replacement is atomic only after `C0_PASS && L2_PASS && L3_WITNESS_FOUND`, the guard is open, the candidate is selected, and commit semantics establish the next-cycle token. Timeout/UNKNOWN before that point leaves the old token untouched. A map, authority, time-index, state-alignment, or tail-consumption mismatch invalidates it and forbids fallback execution.

This is a schema and handoff contract only. No runtime token implementation exists in this task.
