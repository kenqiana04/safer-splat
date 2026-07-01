# Risk-Aware V2 Adaptive Recovery Design

## Method Name

Adaptive Risk-Aware Pre-CBF Candidate Budgeting with Unsafe-State Recovery.

## V2 Versus V1

V1 uses a fixed candidate budget, fixed near threshold, and fixed heading threshold. Its role is mainly computational: it reduces the Gaussian set queried before CBF matrix construction.

V2 dynamically adjusts candidate budget, near threshold, heading threshold, and fallback level according to the current safety criticality. V2 also adds an unsafe or near-unsafe recovery mode. In that mode, the wrapper changes the nominal command passed into the same CBF-QP instead of continuing to use the ordinary goal-tracking nominal command.

The official SAFER-Splat baseline remains unchanged. V2 is implemented only in `work/risk_aware_cbf/` as a reproduction-only wrapper-level prototype.

## Module 1: Safety-Criticality Adaptive Budget Scheduler

The scheduler assigns a step-level criticality level:

```text
if min_h < unsafe_threshold:
    level = RECOVERY
elif min_h < h_recovery:
    level = CRITICAL
elif min_h < h_warning:
    level = WARNING
else:
    level = SAFE
```

Default thresholds:

```text
h_warning = 0.0010
h_recovery = 0.0004
unsafe_threshold = 0.0
```

The criticality signal uses the current full-scene `min_safety_h` queried at the robot state before solving the step. The runner also logs previous-step `min_safety_h`, goal distance delta, control deviation, and active constraints. These additional signals are available for diagnosis, but the default scheduler keeps the rule explicit and threshold-based to avoid hidden tuning. Distance to nearest Gaussian is used by the recovery module and logged in `v2_recovery_debug.csv`.

## Adaptive Budget Schedule

```text
SAFE:
    candidate_budget = 1000
    near_distance_threshold = 0.05
    heading_distance_threshold = 0.20
    fallback_level = none

WARNING:
    candidate_budget = 2000
    near_distance_threshold = 0.08
    heading_distance_threshold = 0.25
    fallback_level = soft

CRITICAL:
    candidate_budget = 5000
    near_distance_threshold = 0.12
    heading_distance_threshold = 0.35
    fallback_level = strong

RECOVERY:
    candidate_budget = full
    near_distance_threshold = 0.15
    heading_distance_threshold = 0.50
    fallback_level = full
```

If full candidate mode is too slow in later experiments, `recovery_budget` can be set to a large integer such as `20000`. That must be reported as high-budget recovery, not full recovery.

## Module 2: Unsafe-State Recovery Mode

Recovery mode does not modify the official CBF or QP implementation. It changes only the nominal command passed into the same CBF-QP.

The recovery nominal command is:

```text
u_recovery = k_repulse * normalize(robot_position - nearest_gaussian_center)
             - k_damp * robot_velocity
```

Default parameters:

```text
k_repulse = 1.0
k_damp = 0.5
```

V2 blends the goal-tracking command and recovery command:

```text
u_nom_v2 = (1 - lambda_recovery) * u_goal + lambda_recovery * u_recovery
```

Default blending:

```text
SAFE: lambda_recovery = 0.0
WARNING: lambda_recovery = 0.0
CRITICAL: lambda_recovery = 0.5
RECOVERY: lambda_recovery = 1.0
```

The wrapper records:

```text
recovery_used
recovery_lambda
recovery_source_gaussian_id
nearest_gaussian_distance
recovery_direction
u_goal
u_recovery
u_nom_v2
```

The recovery source is the nearest Gaussian center, not an exact ellipsoid closest point. It is used only for wrapper-level nominal command construction and is not reported as meter clearance.

## Claim Boundary

V2 does not prove a new CBF theorem.

V2 is a wrapper-level adaptive computation and recovery strategy.

The official SAFER-Splat baseline remains unchanged.

The reported `min_safety_h` is not meter clearance.

Any result on flight trial 57 is a hard-case prototype diagnostic. It is not sufficient for a paper-level robustness claim without broader validation.
