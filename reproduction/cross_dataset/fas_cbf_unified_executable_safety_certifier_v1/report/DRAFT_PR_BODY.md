## Scope

Implements the candidate-level unified certifier frozen by PR #83. PR #83 remains open and unchanged at `17805e67b75412dc21b1a5fff4143ea3bc985f7f`.

## Frozen contracts

- Normative model: `POSITION_FIRST_FORWARD_EULER_DOUBLE_INTEGRATOR_V1`
- Actuator bounds: `[-0.1,0.1]^3`, `dt=0.05`
- Segment: exact isotropic primitive plus conservative signed-distance interval bound; sampled backend diagnostic only
- Terminal: `BRAKING_TO_REST_TERMINAL_SET_V1`, tolerance `1e-12`
- Backup: deterministic componentwise braking
- Typed fail-closed; candidate exhaustion is not unrecoverability

## Evidence

- pytest: 33 passed
- randomized segments: 10000; false-safe: 0
- randomized braking: 2000/2000
- Replica plant-free smoke: 25 states
- reference online reads: 0
- proof status: S1/B1/R1/F1 under explicit assumptions

## Claim boundary

No map training/mutation, navigation rollout, deployment claim, complete `U_exec`, global recursive feasibility, or full-stack superiority claim.

`FINAL_STATUS=PASS_GAUSSIAN_MAP_UNIFIED_EXECUTABLE_SAFETY_CERTIFIER_V1`

`FINAL_DECISION=FREEZE_CERTIFIER_AND_BUILD_MINIMAL_ACTIVATED_REPLICA_GT_BENCHMARK`

Only next task: `BUILD_REPLICA_GT_EXECUTABLE_SAFETY_ACTIVATED_BENCHMARK_V1`
