# FAS-CBF Next Stage Summary

## What was completed

- Synthetic initial near-unsafe / unsafe stress generation.
- Repair-only ablation for no repair, heuristic repulsion, verified projection, and active-set verified projection.
- Stratified post-repair navigation validation when navigation results are available.
- V4-C runtime tuning pilot on hotspot flight trials.

## Synthetic stress generation summary

- Synthetic cases: 120
- Near-unsafe: 15
- Margin-violating: 17
- Unsafe: 88

## Repair-only ablation summary

- Active-set repair success rate: 1.0
- Heuristic repair success rate: 0.9583333333333334
- Active-set full-query verified equals success: True

## Post-repair navigation summary

- Collision count sum: 0
- QP infeasible count sum: 0

## V4-C runtime tuning pilot summary

| config_id | collision_count | qp_infeasible_count | exec_horizon_margin_violation_count | runtime_mean | runtime_ratio_vs_R0 |
| --- | --- | --- | --- | --- | --- |
| R0_H3_N128_baseline | 0 | 0 | 0 | 1.27952 | 1 |
| R1_H3_N64 | 0 | 0 | 0 | 0.799017 | 0.624466 |
| R2_H3_N32 | 0 | 0 | 0 | 0.567821 | 0.443776 |
| R3_H3_N64_conservative | 0 | 0 | 0 | 0.831883 | 0.650152 |
| R4_H2_N64 | 0 | 0 | 0 | 0.517519 | 0.404463 |
| R5_H3_N64_goal_preserving | 0 | 0 | 0 | 0.820329 | 0.641122 |

## Updated claim boundary

This stage remains reproduction-side under `work/risk_aware_cbf/`. It does not modify official SAFER-Splat source code, does not modify `run.py`, does not change collision checks, and does not claim a new CBF theorem. Synthetic perturbed starts are not official benchmark starts, post-repair navigation is not original benchmark navigation, margin violations are not collisions, and `min_safety_h` is the repository GSplat ellipsoid safety h value rather than meter clearance.

## Recommended next action

Pilot-only decision: PROCEED_TO_TUNED_V4C_FULL100.

After the appended R4_H2_N64 full100 validation: PROCEED_TO_METHOD_AND_EXPERIMENT_WRITING.

## Tuned V4-C Full100 Validation

This section was appended after validating R4_H2_N64 on dense flight official100. R4_H2_N64 came from the hotspot runtime tuning pilot, where it was the cheapest safe candidate. The full100 validation was run to test whether the hotspot result generalizes to all official dense-flight start-goal pairs.

| rows | collision_count | collision_free_count | qp_infeasible_count | base_horizon_margin_violation_count | exec_horizon_margin_violation_count | predictive_recovery_used_count | predictive_recovery_success_count | recovery_failed_count | min_safety_h_min | progress_mean | runtime_mean | runtime_p95 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 100 | 0 | 100 | 0 | 193 | 0 | 193 | 193 | 0 | 0.000500013 | 0.448854 | 0.095952 | 0.309428 |

R4_H2_N64 is the recommended practical V4-C configuration for dense flight experiments. H3_N128 can be kept as a robust reference setting. Method/experiment writing can begin, with remaining limitations documented around runtime overhead, reproduction-side wrapper status, and the lack of a new CBF theorem.
