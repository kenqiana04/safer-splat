# Flight Trial 57 Diagnosis Report

## Scope

This report diagnoses the flight trial-57 collision observed in the flight 100-trial run.
It does not modify official SAFER-Splat source code.
It does not claim a new CBF theorem.

## Failure Summary

SAFER-Splat baseline and V1 bestD both collide on flight trial 57.

- baseline min_safety_h_min: -0.0003094291314482
- V1 bestD min_safety_h_min: -0.0003094291314482
- collision step if available: 1
- baseline QP infeasible count: 0
- V1 bestD QP infeasible count: 0

## Stepwise Diagnosis

- min_safety_h trajectory: minimum safety h occurs at the first recorded step for both baseline and V1 bestD.
- control deviation: baseline control_deviation_mean is 0.0387517920490593; V1 bestD control_deviation_mean is 0.0389182429152186; detailed per-step values are in `trial57_stepwise_safety.csv`.
- active constraints: baseline active_constraints_mean is 350.60869565217394; V1 bestD active_constraints_mean is 187.16666666666663.
- candidate counts: V1 bestD candidate_count_final at/near collision is 5282.0; this is not abnormal relative to trial-57 candidate statistics.
- nearby Gaussian properties: written to `trial57_nearby_gaussians.csv`; nearest logged Gaussian center distance is 0.024465207271911454.
- fallback status: V1 bestD fallback_used at/near collision is False.

## Tuning Results

| config_name | method | collision_count | min_safety_h_min | progress_mean | control_deviation_mean | active_constraints_mean | runtime_mean | runtime_p95 | qp_infeasible_count | fallback_used_rate | candidate_count_final_mean | diagnosis_note |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| baseline_reference | safer_splat_filter | 1 | -0.0003094291314 | 0.5209763612 | 0.03875179205 | 350.6086957 | 0.1153211733 | 0.1477107994 | 0 |  |  | Official SAFER-Splat baseline reproduces trial-57 collision. |
| bestD | risk_aware_v1_pre_cbf | 1 | -0.0003094291314 | 0.522682395 | 0.03891824292 | 187.1666667 | 0.0523880048 | 0.05843059011 | 0 | 0 | 11873.45652 | Conservative V1 setting still collides on trial 57. |
| near008 | risk_aware_v1_pre_cbf | 1 | -0.0003094291314 | 0.5226824217 | 0.03891824808 | 202.2681159 | 0.05439355506 | 0.06117106406 | 0 | 0 | 12168.10145 | Conservative V1 setting still collides on trial 57. |
| near008_heading035 | risk_aware_v1_pre_cbf | 1 | -0.0003094291314 | 0.522682395 | 0.03891823619 | 211.2608696 | 0.06051324145 | 0.06707917321 | 0 | 0 | 27477.55797 | Conservative V1 setting still collides on trial 57. |
| budget5000_near008_heading035 | risk_aware_v1_pre_cbf | 1 | -0.0003094291314 | 0.5213638052 | 0.03887634175 | 221.3333333 | 0.06057587216 | 0.06742840232 | 0 | 0 | 28320.51449 | Conservative V1 setting still collides on trial 57. |
| full_fallback_diag | risk_aware_v1_pre_cbf | 1 | -0.0003094291314 | 0.5209763612 | 0.03875179205 | 350.6086957 | 0.1509583265 | 0.1883794948 | 0 | 0 | 281756 | Full-candidate diagnostic still collides; failure is not explained by V1 subset pruning. |

## Interpretation

All tested configurations collide on trial 57, including the official SAFER-Splat baseline and the full-candidate diagnostic. The full-candidate diagnostic uses all available Gaussians at step 1 and still reproduces the collision. This points to a hard baseline/controller/scene-level case rather than a V1 candidate-selection failure.

Increasing the near threshold, widening the heading distance, and increasing candidate budget did not avoid the collision in the single-trial test. No tuned V1 configuration tested here avoids the failure.

Because baseline fails but no V1 tuned setting succeeds, this should be reported as a baseline/controller/scene-level failure for flight trial 57, not as evidence that the V1 subset is too narrow. Any stronger claim would require a new controller-level change or official baseline investigation, which is outside this task.

## Next Decision

KEEP_RESULT_AND_REPORT_BASELINE_FAILURE

Reason: baseline and full-candidate fallback both collide; no tested V1 tuning avoids the failure.
