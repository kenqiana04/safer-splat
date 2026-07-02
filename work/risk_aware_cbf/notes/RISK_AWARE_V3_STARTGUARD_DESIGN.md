# StartGuard V3 Design

## Method Name

StartGuard: Initial Safety Certification and Safe-Start Repair for CBF-Based Navigation in 3D Gaussian Splatting Maps

## Difference From V1 and V2

V1 focuses on pre-CBF candidate budgeting for computational efficiency.

V2 adds adaptive budgeting and wrapper-level recovery after the task has already started.

V3 moves the safety check before task execution and explicitly repairs initial states that violate the CBF safe-set condition.

## Problem Definition

Standard CBF-style safety filtering assumes that the system starts inside or near the safe set. If the initial state already has negative safety value, then a runtime recovery controller cannot remove the initial violation from strict collision metrics.

Flight trial 57 exposes this failure mode: the first recorded safety value is already negative for the baseline, V1, V2, and full-candidate diagnostic. V2 recovery can react after the task starts, but it cannot make the original unsafe sample disappear from a strict collision log.

## V3 Modules

Stage 1: Initial Safety Certification

Before running the planner/controller, StartGuard evaluates the initial state with the same GSplat collision geometry and safety function used by the CBF pipeline. It records the original initial safety value, the most violated Gaussian index, and the trial-level status:

- `initial_safe`
- `initial_near_unsafe`
- `initial_unsafe`

Stage 2: Safe-Start Projection / Repair

When the initial state is below the requested safety margin, StartGuard searches for a nearby repaired start. The default implementation is an iterative multi-Gaussian repulsion projection. At each iteration it queries all Gaussian safety values, takes the lowest-safety Gaussians, builds a weighted direction away from their centers, and moves by a small fixed step.

This repair is gradient-free and intentionally simple. It is a reproduction wrapper prototype, not an optimal projection solver.

Stage 3: Post-Repair Navigation with V1 bestD or baseline CBF-QP

If the repaired start satisfies the safety margin, the wrapper runs navigation from the repaired start while keeping the original goal. Post-repair navigation is reported separately from the original trial result.

## Certification Rule

Let `h0` be the minimum `GSplatLoader.query_distance` safety value at the initial state. StartGuard uses:

```text
if h0 < safety_margin:
    status = initial_unsafe
elif h0 < near_unsafe_margin:
    status = initial_near_unsafe
else:
    status = initial_safe
```

The default thresholds are:

```text
safety_margin = 0.0005
near_unsafe_margin = 0.0010
```

`min_safety_h` is the official GSplatLoader query value used by the local CBF pipeline. It is not meter clearance.

## Repair Rule

The default repair policy is Iterative Multi-Gaussian Repulsion Projection:

```text
direction_i = normalize(x_current - gaussian_center_i)
weight_i = 1 / (distance_i + epsilon)
direction = normalize(sum_i weight_i * direction_i)
x_next = x_current + step_size * direction
```

The selected Gaussians are the lowest-safety Gaussians under the current query, capped by `num_nearby_gaussians`. If the multi-Gaussian direction is degenerate, StartGuard falls back to the single most violated Gaussian.

Default parameters:

```text
max_repair_steps = 100
step_size = 0.005
max_repair_distance = 0.20
num_nearby_gaussians = 20
```

## Claim Boundary

V3 does not prove a new CBF theorem.

V3 does not modify the official SAFER-Splat baseline.

V3 does not erase the original initial violation.

For initially unsafe trials, original initial violation and post-repair navigation are reported separately.

The reported `min_safety_h` is not meter clearance.
