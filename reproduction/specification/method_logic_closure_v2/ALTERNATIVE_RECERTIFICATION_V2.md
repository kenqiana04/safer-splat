# Alternative recertification V2

L4 proposes only; it never commits. Every native, lawful `ALTERNATIVE_PROPOSED_CONTROL` receives a new candidate identity and restarts the complete `C0 → L2 → L3` path under the same state, timebase, map, geometry, and actuator authority.

Eligible causes are candidate-local C0 failure, L2 FAIL, L2 candidate-local UNKNOWN, L3 WITNESS_ABSENT, or L3 candidate-local UNKNOWN, and only when the retained backup is independently VALID, the deadline is OPEN, a lawful pre-frozen source exists, and the finite attempt budget remains. L1 FAIL, global/authority UNKNOWN, map identity failure, and deadline closure are never repaired by changing candidate.

The frozen abstract budget is two attempts for model checking only; it is not a runtime performance parameter authorization. Guard arrival preempts the loop. Exhaustion means no witness in the finite library, not continuous-space infeasibility.
