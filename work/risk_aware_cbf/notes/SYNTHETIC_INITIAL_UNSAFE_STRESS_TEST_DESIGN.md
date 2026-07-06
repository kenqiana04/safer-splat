# Synthetic Initial-Unsafe Stress Test Design

This document defines a future stress test. It is not executed in V4-A.

## Purpose

The current `flight100` benchmark contains only a small number of initial near-unsafe or unsafe starts. A controlled stress test can evaluate whether safe-start projection remains reliable when initial states are deliberately perturbed toward risky GSplat geometry.

## Candidate Construction

1. Select several `initial_safe` trials from the existing flight audit.
2. For each selected start, query the nearest or most risky Gaussian using the official GSplat safety query.
3. Perturb the start toward that Gaussian along controlled offsets:
   - `0.005`
   - `0.010`
   - `0.020`
   - `0.050`
4. Keep the original goal unchanged.
5. Label the perturbed starts as controlled near-unsafe or unsafe starts using full GSplat query verification.

## Methods To Compare

- no repair;
- heuristic StartGuard repulsion;
- `verified_projection`;
- `active_set_verified_projection`.

## Metrics

- repair success rate;
- repair distance;
- repair steps or projection iterations;
- full-query verification pass rate;
- post-repair collision count;
- post-repair `min_safety_h` statistics;
- runtime overhead.

## Execution Boundary

This stress test should only be run after V4-A projection and DT audit are reviewed. It should be reported as a synthetic stress test, not as an official benchmark result.

## Relation to V4-C Flight100 Validation

The synthetic initial-unsafe stress test should be used after V4-C full flight100 validation to evaluate whether FAS-Project generalizes beyond the naturally occurring repair-needed cases in flight100.

It should compare:

- no repair;
- heuristic repulsion;
- active-set verified projection;
- active-set verified projection + V4-C predictive recovery if needed.

This document update only records the planned relation to V4-C flight100 validation. The synthetic stress test is not executed in the V4-C flight100 validation stage.

## Motivation after V4-C Flight100

V4-C H-step predictive recovery has now been validated on dense flight official100. The official100 result preserves 100/100 collision-free navigation and 0 QP infeasible trials while reducing H-step horizon margin violations from 236 to 0. Its main limitation is runtime overhead concentrated in activated trials.

V4-A active projection plus V1 flight100 already repaired the naturally occurring safe-start issues in the 8 repair-needed official flight100 cases. That sample is too small to evaluate whether FAS-Project generalizes beyond naturally occurring starts. The synthetic initial-unsafe stress test deliberately perturbs original `initial_safe` starts toward risky GSplat geometry so that FAS-Project can be tested on more near-unsafe and unsafe initial states.

This is a reproduction-side stress test under `work/risk_aware_cbf/`. Synthetic perturbed starts are not official benchmark starts, and post-repair navigation is not an original benchmark result.

## Synthetic perturbation generation

The generator selects original flight trials whose initial state is certified `initial_safe` by StartGuard and whose `initial_min_safety_h` is at least the configured near-unsafe margin when available. For each selected source trial, it keeps the original goal unchanged and creates perturbed starts:

1. nearest direction: toward the nearest Gaussian center by Euclidean distance;
2. risky direction: toward the most critical / lowest-h Gaussian, falling back to nearest if metadata is unavailable;
3. random directions: fixed-seed random unit directions.

Perturbation magnitudes start with `0.005,0.010,0.020,0.050`. If too few retained cases are produced, the generator may extend to `0.075,0.100` and records that expansion in the generation metrics. Every synthetic start receives a full GSplat safety query and is labeled:

- `synthetic_safe`: `synthetic_initial_h >= near_unsafe_margin`;
- `synthetic_near_unsafe`: `safety_margin <= synthetic_initial_h < near_unsafe_margin`;
- `synthetic_margin_violating`: `0 <= synthetic_initial_h < safety_margin`;
- `synthetic_unsafe`: `synthetic_initial_h < 0`.

Only `synthetic_near_unsafe`, `synthetic_margin_violating`, and `synthetic_unsafe` are retained for the stress test. If the retained set exceeds the configured cap, cases are stratified by category and perturbation magnitude rather than mixed with official starts.

## Repair-only ablation

Repair-only evaluation compares four methods on the retained synthetic starts:

- `no_repair`;
- `heuristic_repulsion`;
- `verified_projection`;
- `active_set_verified_projection`.

The repair-only stage reports `repair_success_count`, `repair_failure_count`, `full_query_verified_count`, `original_initial_h`, `perturbed_initial_h`, `repaired_initial_h`, `repair_distance`, `repair_iterations`, `active_set_final_size`, and `num_candidates_evaluated`. Repair-only success means the repaired initial point passes the configured full-query safety margin. It is not navigation success.

## Post-repair navigation validation

Post-repair navigation is evaluated only on a stratified subset of successful `active_set_verified_projection` cases. Selected cases prioritize synthetic unsafe starts, margin-violating starts, hard repairs with large repair distance, and near-boundary repaired starts whose repaired safety value is close to the safety margin.

The navigation validation keeps synthetic starts separate from official starts and reports:

- active-set verified projection + `risk_aware_v1_bestD`;
- active-set verified projection + `risk_aware_v1_bestD` + V4-C H=3 predictive recovery when enabled.

Core metrics include collision count, QP infeasible count, post-repair `min_safety_h_min`, progress, runtime, base H-step margin violations, executed H-step margin violations, predictive recovery use, predictive recovery success, and recovery failures.

## Relation to V4-C predictive recovery

FAS-Project addresses initial feasibility by repairing the starting point before navigation. V4-C FAS-Recover addresses sampled-data H-step horizon margin violations during navigation. These are complementary layers. The synthetic stress test may use V4-C only after active-set safe-start repair, and only as a post-repair navigation validation layer.

If V1 post-repair navigation has H-step margin violations and V4-C reduces them, this supports using V4-C as an empirical predictive recovery wrapper after safe-start repair. It does not convert synthetic post-repair navigation into an official benchmark result.

## Claim boundary

This stage does not modify official SAFER-Splat source code and does not modify `run.py`. It does not change collision checks. It does not claim a new CBF theorem.

`min_safety_h` is the repository GSplat ellipsoid safety h value returned by the SAFER-Splat query path. It is not metric clearance in meters, and it must not be mixed with Splat-Nav signed clearance. Synthetic perturbed starts are not official benchmark starts, post-repair navigation is not original benchmark navigation, margin violations are not collisions, and collision-free behavior must be reported separately from H-step margin satisfaction.
