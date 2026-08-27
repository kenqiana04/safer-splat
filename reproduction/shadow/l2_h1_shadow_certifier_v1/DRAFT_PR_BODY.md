## Scope

Implements a task-local, shadow-only L2/H1 certifier from exact PR #93 head `1df09c56eedb53d46f9347695026086319738a89`. PR #83–#93 and all 17 protected raw Git blobs remain unchanged.

## Frozen contract and implementation

- `POSITION_FIRST_FORWARD_EULER_DOUBLE_INTEGRATOR_V1`
- `p_k1 = p_k + dt*v_k`
- `p_k2 = p_k + 2dt*v_k + dt²*u_k`
- candidate-sensitive full `Segment(p_k1,p_k2)`
- direct frozen `EXACT_ANALYTIC_SPHERE_SEGMENT_MINIMUM` and `CONSERVATIVE_SIGNED_DISTANCE_LIPSCHITZ_INTERVAL` calls
- `DENSE_SAMPLED_DIAGNOSTIC_ONLY` remains diagnostic-only
- endpoint fallback disabled
- snapshot ID/hash/stale/context and robot radius 0.10 m + margin 0.01 m contracts enforced
- typed PASS/FAIL/UNKNOWN; UNKNOWN is semantically fail-closed but causes no runtime intervention

## Authority and validation

Controller, execution, candidate-selection, alternative, backup, terminal, and fail-close authority are all false. L3/L4/L5/H2 are absent. Unit, O1–O10 analytical, direct differential, candidate-sensitivity, endpoint-trap, diagnostic-independence, determinism, and four reviewer checks pass. No formal navigation run or performance claim was made.

`FINAL_STATUS=PASS_L2_H1_SHADOW_CERTIFIER_IMPLEMENTATION_V1`

`FINAL_DECISION=FREEZE_SHADOW_IMPLEMENTATION_AND_VALIDATE_ON_FROZEN_REPLAY`

Only next task: `VALIDATE_L2_H1_SHADOW_CERTIFIER_ON_FROZEN_REPLAY_V1` (not started).
