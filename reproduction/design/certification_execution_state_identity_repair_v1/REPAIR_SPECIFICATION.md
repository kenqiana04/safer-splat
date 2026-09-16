# Repair Specification

## Frozen diagnosis

The repair addresses only `COMMON_FLOAT32_REALIZATION_IDENTITY_GAP`: certification currently constructs predicted states with host binary64 expressions while committed execution realizes the position-first Euler transition through the actual torch float32 execution path. A one-ULP endpoint difference can therefore make a predecessor L2 endpoint differ from the next cycle's realized L1 endpoint. The existing `FAIL_V3_HARD_SAFETY_GATE` result is preserved.

## Canonical primitive

The implementation SHALL introduce one side-effect-free deterministic transition service:

`T_exec(x, u, dt, arithmetic_identity) -> x_next`

Its numerical graph SHALL be bitwise-equivalent to the actual plant realization for the same runtime device and serialization contract:

1. construct state and action tensors using the frozen execution dtype;
2. evaluate the frozen position-first forward-Euler double-integrator derivative;
3. evaluate the exact operation order `x + derivative * dt` used by the plant;
4. serialize the realized tensor through the same scalar conversion contract used by committed snapshots.

The service SHALL NOT commit a plant action, mutate a token, append a trace, invoke a controller or QP, or own routing. `PlantCommitAdapter` remains the sole plant side-effect owner and consumes this same pure primitive. Device, dtype, operation graph, dynamics, timebase, and serialization identities are mandatory authority fields. A backend/device for which bitwise equivalence has not been established is not interchangeable and fails closed.

## L1 construction

L1 SHALL use a canonical, candidate-independent immediate-position primitive `T_pos_exec(x, dt)` derived from the same execution graph. Under the frozen dynamics,

`position(T_exec(x, u_a, dt)) == position(T_exec(x, u_b, dt))`

bitwise for every admissible `u_a`, `u_b`. This is a required proof, not an assumed algebraic simplification. L1 SHALL evaluate the canonical segment from current position to `T_pos_exec`; it SHALL NOT introduce candidate authority.

## L2 construction

L2 SHALL use sequential canonical transitions rather than a host-binary64 closed form:

`x_k1 = T_exec(x_k, u_k, dt)`

`p_k1 = position(x_k1)`

`x_k2 = T_exec(x_k1, u_position_irrelevant, dt)`

`p_k2 = position(x_k2)`

The second-step action is position-irrelevant only because this is proven under the frozen position-first dynamics. The implementation may expose an equivalent `T_pos_exec(x_k1, dt)` only after bitwise equivalence is proven. No dynamics, dt, controller, policy, or horizon changes are authorized.

## L3, backup, terminal, and segment construction

All predicted state construction used by L3 witnesses, backup certification, terminal certification, sampled segment certification, braking tails, recovery paths, and retained-token validation SHALL consume the same canonical transition service or a bitwise-proven projection of it. A prepared backup bundle SHALL bind transition arithmetic identity, dtype/device identity, dynamics/timebase identity, state identities, action identities, and segment endpoint identities. Token activation and cursor advancement remain owned by the existing runtime lifecycle.

## Start admission and current-state paths

StartAdmission performs a current-state query and does not require predictive arithmetic migration. It SHALL nevertheless bind the canonical serialized state identity and expose the same identity vocabulary so that a current-state result cannot be joined to a different realized snapshot.

## Identity and mismatch semantics

Every certificate-bearing segment SHALL carry:

- source realized-state identity;
- action/candidate identity when causally relevant;
- transition arithmetic identity;
- dtype/device identity;
- dynamics and timebase identity;
- predicted endpoint identities;
- map and geometry authority identities;
- certificate evidence identity.

Comparison produces exactly one typed state: `CERT_EXEC_STATE_IDENTITY_MATCH` or `CERT_EXEC_STATE_IDENTITY_MISMATCH`. A mismatch is never PASS, never silently repaired, and never allowed to acquire or retain commit authority. It yields a typed fail-closed/UNKNOWN evidence result, invalidates the affected newly prepared bundle or retained-token use, and returns control to existing Supervisor routing/fallback/boundary authority. It SHALL NOT itself commit a plant action or change selection priority.

## Trace and evidence

Trace evidence SHALL record canonical transition identity, source and predicted state identities, selected/executed action identity, certificate segment identities, the match/mismatch status, and completeness. Evidence logging is observational: a logging failure cannot create action authority. If required evidence cannot be durably recorded, the affected path is ineligible for scientific evaluation and follows the frozen runtime trace-integrity policy.

## No policy drift

This repair does not alter 0.015 q hard radius, zero runtime margin, zero rho, controller/QP, actuator limits, map, query backend, dynamics equations, dt, candidate generation, Supervisor priority, backup/terminal policy, deadline policy, or experiment/statistical contracts. The 0.025 q historical shell remains diagnostic-only with no runtime authority.

## Archived offline acceptance

For archived trials 22, 28, 57, and 59 only, offline reconstruction SHALL demonstrate that repaired canonical L2 endpoints and the corresponding next realized L1 endpoints are bitwise identical and are passed to the certifier as the same segment. Certificate verdicts may remain FAIL; this is a correctness requirement, not an efficacy correction and not a rerun of the frozen experiment.
