# V4-C Flight100 Validation and Runtime Breakdown

## Scope

This report evaluates V4-C H-step predictive safety recovery on dense flight official100.
It is a reproduction-side wrapper evaluation under `work/risk_aware_cbf/`.
It does not modify official SAFER-Splat source code.
It does not claim a new CBF theorem.
It is not a full SAFER-Splat paper reproduction.

## Method

The tested FAS-CBF pipeline combines:

- FAS-Certify: initial feasibility certification.
- FAS-Project: V4-A active-set safe-start projection.
- FAS-Budget: Risk-Aware V1 bestD candidate budgeting.
- FAS-Verify: H-step sampled-data safety verification.
- FAS-Correct: V4-B one-step correction, retained as a negative result.
- FAS-Recover: V4-C H-step predictive recovery.

V4-B failed because one-step acceleration correction could not affect immediate position safety under the current Euler double-integrator rollout. V4-C uses H-step rollout so acceleration can influence future positions through velocity. The full100 run uses H=3, `num_sequences=128`, `activation_mode=on_margin_violation`, `dt_margin=0.0005`, and Risk-Aware V1 bestD. Only the first control of the selected sequence is executed, and planning is repeated at every step.

## Full100 Result

| metric | value |
|---|---:|
| rows | 100 |
| collision_count | 0 |
| collision_free_count | 100 |
| qp_infeasible_count | 0 |
| base_horizon_margin_violation_count | 236 |
| exec_horizon_margin_violation_count | 0 |
| reduction | 236 |
| predictive_recovery_used_count | 236 |
| predictive_recovery_success_count | 236 |
| recovery_failed_count | 0 |
| min_safety_h_min | 0.0005000508390367 |
| progress_mean | 0.448789479637711 |
| runtime_mean | 0.1703880064476623 |
| runtime_p95 | 0.7025225639138373 |
| runtime_max | 1.6383513615262757 |
| activated_trial_count | 19 |
| non_activated_trial_count | 81 |

## Runtime Breakdown

V4-C improves horizon margin safety but introduces sequence-evaluation overhead.
Compared with V4-A active projection + V1 flight100, runtime_mean changes from 0.0575582084727561 to 0.1703880064476623 seconds, a 2.960x ratio. Runtime p95 changes from 0.0643087376793846 to 0.7025225639138373 seconds, a 10.924x ratio.

| metric | value |
|---|---:|
| runtime_mean | 0.1703880064476623 |
| runtime_median | 0.05785421744434435 |
| runtime_p75 | 0.060322100377140725 |
| runtime_p90 | 0.41911311704639587 |
| runtime_p95 | 0.900793402513594 |
| runtime_p99 | 1.5050773122211298 |
| runtime_max | 1.6383513615262757 |
| activated_runtime_mean | 0.6527985584409247 |
| activated_runtime_p95 | 1.5171931348852332 |
| activated_runtime_max | 1.6383513615262757 |
| non_activated_runtime_mean | 0.05722997573319334 |
| non_activated_runtime_p95 | 0.0608596625693497 |
| non_activated_runtime_max | 0.0619608878820057 |

Top 5 slowest trials:

|trial|runtime_mean|runtime_p95|runtime_max|predictive_recovery_used_count|predictive_recovery_success_count|recovery_failed_count|base_horizon_margin_violation_count|exec_horizon_margin_violation_count|goal_distance_reduction_ratio|min_safety_h|
|---|---|---|---|---|---|---|---|---|---|---|
|85|1.63835|7.98256|8.16145|34|34|0|34|0|0.304403|0.000500098|
|31|1.50373|8.14013|8.88877|26|26|0|26|0|0.371118|0.000500501|
|13|1.35847|8.00152|8.08269|28|28|0|28|0|0.341208|0.000501377|
|12|1.25886|8.05168|8.17988|24|24|0|24|0|0.34432|0.000500535|
|14|0.998603|7.92719|8.02547|8|8|0|8|0|0.0901941|0.000503154|

Top 5 most activated trials:

|trial|runtime_mean|runtime_p95|runtime_max|predictive_recovery_used_count|predictive_recovery_success_count|recovery_failed_count|base_horizon_margin_violation_count|exec_horizon_margin_violation_count|goal_distance_reduction_ratio|min_safety_h|
|---|---|---|---|---|---|---|---|---|---|---|
|85|1.63835|7.98256|8.16145|34|34|0|34|0|0.304403|0.000500098|
|37|0.895646|8.14636|8.41158|32|32|0|32|0|0.988171|0.000500233|
|13|1.35847|8.00152|8.08269|28|28|0|28|0|0.341208|0.000501377|
|31|1.50373|8.14013|8.88877|26|26|0|26|0|0.371118|0.000500501|
|12|1.25886|8.05168|8.17988|24|24|0|24|0|0.34432|0.000500535|

The runtime overhead is dominated by activated trials that repeatedly evaluate H-step candidate sequences. Therefore V4-C is better used as an on-warning or on-margin recovery module rather than an always-on default controller. Current activation is already `on_margin_violation`, but the per-activation candidate evaluation cost should be optimized before treating it as a cheap default component.

## Comparison With Previous Stages

|run|rows|collision_count|collision_free_count|qp_infeasible_count|base_horizon_margin_violation_count|exec_horizon_margin_violation_count|reduction|predictive_recovery_used_count|predictive_recovery_success_count|recovery_failed_count|min_safety_h_min|progress_mean|runtime_mean|runtime_p95|
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
|V4-A active projection + V1 flight100|100|0|100|0|NA|NA|NA|NA|NA|NA|0.000197846|0.452088|0.0575582|0.0643087|
|V4-C H=3 repair-needed 8|8|0|8|0|9|0|9|9|9|0|0.000500075|0.55028|0.104847|0.0697252|
|V4-C H=3 flight20|20|0|20|0|60|0|60|60|60|0|0.000500535|0.209814|0.241792|1.33275|
|V4-C H=3 flight100|100|0|100|0|236|0|236|236|236|0|0.000500051|0.448789|0.170388|0.702523|

V4-A is a navigation baseline / post-repair safety filtering result. It does not contain H-step predictive audit fields, so those entries are `NA` rather than inferred. V4-C repair-needed 8, flight20, and flight100 are H-step predictive recovery evaluations.

## Honest Interpretation

V4-C full100 preserves collision-free behavior: collision_count is 0 and collision_free_count is 100.
V4-C full100 preserves QP feasibility: qp_infeasible_count is 0.
V4-C full100 removes tested H-step horizon margin violations under the chosen dt_margin: base violations are 236 and executed violations are 0.
Recovery failures are reported directly: recovery_failed_count is 0.

Margin violations are not collisions. Collision-free behavior and margin-satisfying behavior are reported separately. The minimum safety value remains nonnegative, with min_safety_h_min=0.0005000508390367.

## Claim Boundary

No official SAFER-Splat source code is modified.
No new CBF theorem is claimed.
`min_safety_h` is not meter clearance.
The safety value is the repository's GSplat ellipsoid safety h value.
V4-C is an empirical sampling-based predictive recovery wrapper unless formal assumptions are later proved.
Post-repair navigation is not original benchmark navigation.
This is dense flight reproduction-side validation, not full SAFER-Splat paper reproduction.

## Next Decision

Recommended decision: **PROCEED_TO_SYNTHETIC_INITIAL_UNSAFE_STRESS_TEST and TUNE_V4C_RUNTIME_OVERHEAD**.

Module recommendation: **warning-triggered module**.

Runtime overhead assessment: **high**.

Because full100 has collision_count=0, qp_infeasible_count=0, exec_horizon_margin_violation_count=0, and recovery_failed_count=0, the synthetic initial-unsafe stress test can be planned next. Because runtime overhead is high, runtime tuning should be done before presenting V4-C as a default always-on module.
