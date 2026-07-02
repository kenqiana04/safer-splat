# V4-A Active Projection and Discrete-Time Safety Audit Report

## Scope

This report evaluates V4-A: verified safe-start projection and log-only discrete-time safety verification. It does not modify official SAFER-Splat source code. It does not claim a new CBF theorem.

## Method

The V4-A layer is organized as FAS-CBF: initial certification, verified safe-start projection, risk-aware V1 bestD candidate budgeting, and log-only one-step discrete-time safety audit. Active-set projection uses nearby or violated Gaussian IDs to seed candidate directions, but every accepted repair is checked with the full GSplat safety query.

## Projection Ablation

|method|rows|repair_success_count|repair_failure_count|repair_distance_mean|repair_distance_p95|repair_distance_max|projection_iterations_mean|num_candidates_evaluated_mean|full_query_verified_count|
|---|---|---|---|---|---|---|---|---|---|
|active_set_verified_projection|8|8|0|0.005625000659245944|0.016499996466496455|0.01999999494050517|0.625|536.25|8|
|repulsion|8|8|0|0.004999757520345377|0.013249036446282034|0.014999078278396794|1.0|1.0|8|
|verified_projection|8|8|0|0.005625000659245944|0.016499996466496455|0.01999999494050517|0.625|536.25|8|


## Flight100 Navigation

|section|rows|navigation_executed_count|collision_count|collision_free_count|min_safety_h_min|progress_mean|runtime_mean|runtime_p95|qp_infeasible_count|repair_used_count|repair_distance_mean|
|---|---|---|---|---|---|---|---|---|---|---|---|
|v4_active_projection_flight100|100|100|0|100|0.00019784551113843918|0.45208792380405577|0.05755820847275613|0.06430873767938465|0|8|0.005625000659245944|
|startguard_heuristic_reference|100|100|0|100|0.00019784551113843918|0.45205064332574657|0.05795951384430193|0.06526291041448712|0|8|0.004999758638790424|


## DT Safety Audit

|section|rows|num_steps|predicted_next_violation_count|actual_next_violation_count|min_current_h|min_predicted_next_h|min_actual_next_h|prediction_error_mean|prediction_error_p95|
|---|---|---|---|---|---|---|---|---|---|
|dt_repair_needed|8|1183|21|21|0.00041247426997870207|0.00041247426997870207|0.00041247426997870207|0.0|0.0|
|dt_flight20|20|1735|93|93|0.00032773660495877266|0.00032773660495877266|0.00032773660495877266|0.0|0.0|


## Honest Interpretation

If active-set projection succeeds, it supports replacing heuristic StartGuard repair with a verified safe-start projection module. If active-set projection does not improve repair distance, the main gain is verification and formalization rather than shorter displacement. If the DT audit finds no predicted or actual next-step violation, the log-only audit did not reveal a sampled-data violation in the tested runs. If it finds a violation, that motivates V4-B corrective sampled-data control. Post-repair results remain separate from original benchmark results.

## Claim Boundary

- No official SAFER-Splat source code is modified.
- No new CBF theorem is claimed.
- `min_safety_h` is not meter clearance.
- Verified projection is only locally and empirically verified by full GSplat safety query unless formal conditions are proved.
- Post-repair navigation is not the same as original benchmark navigation.

## Next Decision

Recommended decision: `PROCEED_TO_V4B_CORRECTIVE_DT_FILTER`.
