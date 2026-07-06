# Tuned V4-C Full100 Validation with R4_H2_N64

## Scope

This report evaluates the tuned V4-C R4_H2_N64 configuration on dense flight official100. It is a reproduction-side wrapper evaluation under `work/risk_aware_cbf/`. It does not modify official SAFER-Splat source code, does not claim a new CBF theorem, and is not a full SAFER-Splat paper reproduction. It validates a tuned configuration suggested by the hotspot runtime tuning pilot.

## Method

The evaluation uses the FAS-CBF framework with V4-A active-set safe-start projection and Risk-Aware V1 bestD navigation. V4-B one-step correction is retained as a negative result because acceleration correction cannot affect immediate position safety; V4-C H-step predictive recovery works by rolling out future positions so acceleration affects future safety through velocity. The original robust V4-C setting is H3_N128. The tuned setting evaluated here is R4_H2_N64 with horizon=2, num_sequences=64, activation_mode=on_margin_violation, dt_margin=0.0005, w_goal=0.2, w_safety=10.0. Only the first control of the selected sequence is executed and the controller replans at every step.

## Tuned Full100 Result

| rows | collision_count | collision_free_count | qp_infeasible_count | base_horizon_margin_violation_count | exec_horizon_margin_violation_count | reduction | predictive_recovery_used_count | predictive_recovery_success_count | recovery_failed_count | min_safety_h_min | progress_mean | runtime_mean | runtime_p95 | runtime_max | activated_trial_count | non_activated_trial_count |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 100 | 0 | 100 | 0 | 193 | 0 | 193 | 193 | 193 | 0 | 0.000500013 | 0.448854 | 0.095952 | 0.309428 | 0.654511 | 19 | 81 |

## Runtime Comparison

| run | runtime_mean | runtime_p95 | runtime_max | runtime_mean_ratio_vs_V4A | runtime_mean_ratio_vs_H3_N128 |
| --- | --- | --- | --- | --- | --- |
| V4-A active projection + V1 flight100 | 0.057558 | 0.064309 | 0.064539 | 1 | 0.337807 |
| V4-C H3_N128 full100 | 0.170388 | 0.702523 | 1.638351 | 2.960273 | 1 |
| V4-C R4_H2_N64 hotspot pilot | 0.517519 | 0.649463 | 0.666929 | 8.991223 | 3.037295 |
| V4-C R4_H2_N64 tuned full100 | 0.095952 | 0.309428 | 0.654511 | 1.667038 | 0.563137 |

R4_H2_N64 reduces sequence-evaluation overhead relative to H3_N128. However, because it still runs H-step predictive recovery on activated steps, it remains slower than V4-A active projection + V1. V4-C should remain warning-triggered rather than always-on.

### Top 5 Slowest Trials

| trial | runtime_mean | runtime_p95 | predictive_recovery_used_count | predictive_recovery_success_count | recovery_failed_count | base_horizon_margin_violation_count | exec_horizon_margin_violation_count | goal_distance_reduction_ratio | min_safety_h |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 85 | 0.654511 | 3.401781 | 30 | 30 | 0 | 30 | 0 | 0.303182 | 0.00050002 |
| 13 | 0.593209 | 3.421564 | 28 | 28 | 0 | 28 | 0 | 0.348974 | 0.000500013 |
| 31 | 0.566694 | 3.415046 | 22 | 22 | 0 | 22 | 0 | 0.36863 | 0.000500028 |
| 14 | 0.450985 | 3.378476 | 8 | 8 | 0 | 8 | 0 | 0.09139 | 0.000500029 |
| 37 | 0.391892 | 3.416798 | 30 | 30 | 0 | 30 | 0 | 0.987913 | 0.000500027 |

### Top 5 Most Activated Trials

| trial | predictive_recovery_used_count | predictive_recovery_success_count | recovery_failed_count | runtime_mean | runtime_p95 | base_horizon_margin_violation_count | exec_horizon_margin_violation_count | goal_distance_reduction_ratio | min_safety_h |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 37 | 30 | 30 | 0 | 0.391892 | 3.416798 | 30 | 0 | 0.987913 | 0.000500027 |
| 85 | 30 | 30 | 0 | 0.654511 | 3.401781 | 30 | 0 | 0.303182 | 0.00050002 |
| 13 | 28 | 28 | 0 | 0.593209 | 3.421564 | 28 | 0 | 0.348974 | 0.000500013 |
| 31 | 22 | 22 | 0 | 0.566694 | 3.415046 | 22 | 0 | 0.36863 | 0.000500028 |
| 12 | 16 | 16 | 0 | 0.391344 | 3.393403 | 16 | 0 | 0.349691 | 0.000500075 |

## Comparison With Previous Stages

| run | rows | collision_count | collision_free_count | qp_infeasible_count | horizon | num_sequences | base_horizon_margin_violation_count | exec_horizon_margin_violation_count | reduction | predictive_recovery_used_count | predictive_recovery_success_count | recovery_failed_count | min_safety_h_min | progress_mean | runtime_mean | runtime_p95 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| V4-A active projection + V1 flight100 | 100 | 0 | 100 | 0 | NA | NA | NA | NA | NA | NA | NA | NA | 0.000197846 | 0.452088 | 0.057558 | 0.064309 |
| V4-C H3_N128 full100 | 100 | 0 | 100 | 0 | 3 | 128 | 236 | 0 | 236 | 236 | 236 | 0 | 0.000500051 | 0.448789 | 0.170388 | 0.702523 |
| V4-C R4_H2_N64 hotspot pilot | 6 | 0 | NA | 0 | 2 | 64 | 134 | 0 | 134 | 134 | 134 | 0 | 0.000500013 | 0.408297 | 0.517519 | 0.649463 |
| V4-C R4_H2_N64 tuned full100 | 100 | 0 | 100 | 0 | 2 | 64 | 193 | 0 | 193 | 193 | 193 | 0 | 0.000500013 | 0.448854 | 0.095952 | 0.309428 |

V4-A is the high-efficiency post-repair navigation baseline and does not provide H-step predictive audit fields. H3_N128 is the robust predictive recovery reference. R4_H2_N64 tests whether a shorter horizon and fewer sequences preserve margin satisfaction with lower runtime.

## Honest Interpretation

Tuned R4 full100 keeps collision_count=0 and qp_infeasible_count=0, supporting R4 as a valid tuned predictive recovery configuration in the tested dense flight setting. Its exec_horizon_margin_violation_count is 0, so it removes tested H-step horizon margin violations under dt_margin=0.0005. Its runtime is much lower than H3_N128, so R4 can be recommended as the practical dense-flight V4-C configuration. Margin violations are not collisions; collision-free and margin-satisfying behavior are reported separately.

## Claim Boundary

No official SAFER-Splat source code is modified. No new CBF theorem is claimed. `min_safety_h` is not meter clearance; it is the repository GSplat ellipsoid safety h value. V4-C is an empirical sampling-based predictive recovery wrapper unless formal assumptions are later proved. Post-repair navigation is not original benchmark navigation. This is dense flight reproduction-side validation, not full SAFER-Splat paper reproduction. R4_H2_N64 was tuned on hotspot pilot and validated here on dense flight official100.

## Next Decision

PROCEED_TO_METHOD_AND_EXPERIMENT_WRITING

R4_H2_N64 is the recommended practical V4-C configuration for dense flight experiments. H3_N128 should be kept as a robust reference setting.
