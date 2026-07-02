# V4-B: Corrective Discrete-Time Safety Filter for FAS-CBF

## Motivation

V4-A log-only DT audit found next-step safety margin violations under `safety_margin=0.0005`. These violations are not collisions, but they indicate that the one-step executed trajectory can fall below the desired discrete-time safety margin.

V4-B introduces a corrective sampled-data safety filter. It checks the one-step rollout of the baseline control and selects an alternative local control when the predicted next-step safety margin is below the threshold.

## Relationship To V4-A

V4-A detects sampled-data margin violations. V4-B uses one-step rollout and local control sampling to correct controls before execution.

V4-B does not replace SAFER-Splat CBF-QP. It wraps the output of SAFER-Splat / V1 bestD and only intervenes when the predicted next-step safety margin is below threshold.

## Control Problem

Given current state `x_t` and nominal safe control `u_base` from SAFER-Splat or V1 bestD, predict:

```text
x_{t+1} = f_d(x_t, u_base)
```

If:

```text
h(x_{t+1}) >= delta_dt
```

then execute `u_base`.

If:

```text
h(x_{t+1}) < delta_dt
```

sample candidate controls around `u_base` and `u_nom`, then choose a candidate `u_corr` such that:

```text
h(f_d(x_t, u_corr)) >= delta_dt
```

with minimum cost:

```text
||u_corr - u_base||^2
+ w_goal * goal_tracking_cost
+ w_smooth * ||u_corr - u_prev||^2
```

If no candidate satisfies the margin, choose the candidate with maximum predicted-next `h` and record `correction_failed=True`. The failure is not hidden.

## Candidate Controls

The prototype samples:

- scaled versions of `u_base`;
- braking controls based on current velocity;
- repulsive controls away from the current most critical Gaussian;
- goal-directed controls based on the nominal controller;
- fixed-seed random perturbations around `u_base`.

All accepted corrective controls are verified with the same full GSplat safety query used in the previous V4-A audit.

## Claim Boundary

- V4-B is a sampled-data corrective wrapper.
- It does not prove a new CBF theorem.
- It does not modify official SAFER-Splat source.
- The guarantee is empirical one-step full-query verification unless formal assumptions are later proved.
- `min_safety_h` is not meter clearance.
- Margin violations and collisions are reported separately.
