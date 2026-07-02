# V4-A Analysis

Generated at: 2026-07-02T13:27:48

## Projection Trial57

|method|rows|repair_success_count|repair_distance_mean|repair_distance_p95|repair_distance_max|full_query_verified_count|
|---|---|---|---|---|---|---|
|active_set_verified_projection|1|1|0.01999999494050517|0.01999999494050517|0.01999999494050517|1|
|repulsion|1|1|0.014999078278396794|0.014999078278396794|0.014999078278396794|1|
|verified_projection|1|1|0.01999999494050517|0.01999999494050517|0.01999999494050517|1|


## Repair-Needed Projection Ablation

|method|rows|repair_success_count|repair_failure_count|repair_distance_mean|repair_distance_p95|repair_distance_max|projection_iterations_mean|num_candidates_evaluated_mean|full_query_verified_count|
|---|---|---|---|---|---|---|---|---|---|
|active_set_verified_projection|8|8|0|0.005625000659245944|0.016499996466496455|0.01999999494050517|0.625|536.25|8|
|repulsion|8|8|0|0.004999757520345377|0.013249036446282034|0.014999078278396794|1.0|1.0|8|
|verified_projection|8|8|0|0.005625000659245944|0.016499996466496455|0.01999999494050517|0.625|536.25|8|


## Navigation

|section|rows|navigation_executed_count|collision_count|collision_free_count|min_safety_h_min|progress_mean|runtime_mean|runtime_p95|qp_infeasible_count|repair_used_count|repair_distance_mean|
|---|---|---|---|---|---|---|---|---|---|---|---|
|v4_active_projection_flight100|100|100|0|100|0.00019784551113843918|0.45208792380405577|0.05755820847275613|0.06430873767938465|0|8|0.005625000659245944|
|startguard_heuristic_reference|100|100|0|100|0.00019784551113843918|0.45205064332574657|0.05795951384430193|0.06526291041448712|0|8|0.004999758638790424|


## DT Audit

|section|rows|num_steps|predicted_next_violation_count|actual_next_violation_count|min_current_h|min_predicted_next_h|min_actual_next_h|prediction_error_mean|prediction_error_p95|
|---|---|---|---|---|---|---|---|---|---|
|dt_repair_needed|8|1183|21|21|0.00041247426997870207|0.00041247426997870207|0.00041247426997870207|0.0|0.0|
|dt_flight20|20|1735|93|93|0.00032773660495877266|0.00032773660495877266|0.00032773660495877266|0.0|0.0|


## Key Answers

- active_set_verified_projection solves trial57: True
- active_set_verified_projection succeeds on all repair-needed trials: True
- full-query verification passed for active-set rows: True
- DT audit predicted next-step violations: 114
- DT audit actual next-step violations: 114
- recommended decision: PROCEED_TO_V4B_CORRECTIVE_DT_FILTER
