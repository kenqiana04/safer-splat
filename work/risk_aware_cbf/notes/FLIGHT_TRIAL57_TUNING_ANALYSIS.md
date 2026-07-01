# Flight Trial 57 Tuning Analysis

Generated: 2026-07-01T15:29:09

## Tuning Summary

| config_name | method | collision_count | min_safety_h_min | progress_mean | control_deviation_mean | active_constraints_mean | runtime_mean | runtime_p95 | qp_infeasible_count | fallback_used_rate | candidate_count_final_mean | diagnosis_note |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| baseline_reference | safer_splat_filter | 1 | -0.0003094291314 | 0.5209763612 | 0.03875179205 | 350.6086957 | 0.1153211733 | 0.1477107994 | 0 |  |  | Official SAFER-Splat baseline reproduces trial-57 collision. |
| bestD | risk_aware_v1_pre_cbf | 1 | -0.0003094291314 | 0.522682395 | 0.03891824292 | 187.1666667 | 0.0523880048 | 0.05843059011 | 0 | 0 | 11873.45652 | Conservative V1 setting still collides on trial 57. |
| near008 | risk_aware_v1_pre_cbf | 1 | -0.0003094291314 | 0.5226824217 | 0.03891824808 | 202.2681159 | 0.05439355506 | 0.06117106406 | 0 | 0 | 12168.10145 | Conservative V1 setting still collides on trial 57. |
| near008_heading035 | risk_aware_v1_pre_cbf | 1 | -0.0003094291314 | 0.522682395 | 0.03891823619 | 211.2608696 | 0.06051324145 | 0.06707917321 | 0 | 0 | 27477.55797 | Conservative V1 setting still collides on trial 57. |
| budget5000_near008_heading035 | risk_aware_v1_pre_cbf | 1 | -0.0003094291314 | 0.5213638052 | 0.03887634175 | 221.3333333 | 0.06057587216 | 0.06742840232 | 0 | 0 | 28320.51449 | Conservative V1 setting still collides on trial 57. |
| full_fallback_diag | risk_aware_v1_pre_cbf | 1 | -0.0003094291314 | 0.5209763612 | 0.03875179205 | 350.6086957 | 0.1509583265 | 0.1883794948 | 0 | 0 | 281756 | Full-candidate diagnostic still collides; failure is not explained by V1 subset pruning. |

## Required Judgements

- baseline collision reproduced: True
- V1 bestD collision reproduced: True
- near threshold 0.08 solves collision: False
- heading distance 0.35 solves collision: False
- candidate budget 5000 solves collision: False
- full fallback diagnostic collision: True
- any tuned V1 config avoids collision: False
- failure type: baseline/controller/scene-level hard case
- recommended decision: KEEP_RESULT_AND_REPORT_BASELINE_FAILURE

## Diagnosis Context

- collision/min-safety step: 1
- V1 candidate_count_final at step 1: 5282.0
- V1 fallback_used at step 1: False
- V1 forced near at step 1: 624.0
- V1 forced heading at step 1: 4649.0
- baseline/V1 position delta mean: 0.001243502203156135
- baseline/V1 position delta max: 0.0040908053519328755

The trial-57 minimum safety value occurs at the first recorded step. The exact step-0 start state is not available in the logged CSV, so the first recorded post-step position is reported in the diagnosis outputs.
