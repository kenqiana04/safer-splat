# V4-B Analysis

Generated at: 2026-07-02T13:52:43

## DT Prediction Source

- prediction_type: `independent_dynamics_rollout`
- independent_rollout_available: `True`
- actual_next_source: `recorded_trajectory_next_row`
- prediction_error_mean: `0.00018584718942260908`
- prediction_error_p95: `0.0006002016249112785`

## Main Results

|section|num_steps|base_margin_violation_count|exec_margin_violation_count|collision_count|qp_infeasible_count|progress_mean|runtime_mean|runtime_p95|correction_used_count|correction_success_count|correction_failed_count|control_delta_mean|
|---|---|---|---|---|---|---|---|---|---|---|---|---|
|v4a_audit_repair_needed|1183|21|21||||||||||
|v4b_repair_needed|1197|15|15|0|0|0.5502362844303678|0.06920030725147278|0.2458211361197755|15|0|15|0.00046338405295768203|
|v4a_audit_flight20|1735|93|93||||||||||


## Sweep

Best sweep config: `not_executed`

## Key Interpretation

- V4-B reduces repair-needed next-step margin violations: `False`
- V4-B preserves collision-free in repair-needed result: `True`
- V4-B preserves QP infeasible count 0 in repair-needed result: `True`
- repair-needed correction h_improvement_mean: `0.0`
- repair-needed correction h_improvement_max: `0.0`
- recommended decision: `PROCEED_TO_HSTEP_PREDICTIVE_RECOVERY`

## Structural Limitation Observed

For the tested one-step corrective wrapper, the selected corrective controls did not improve the one-step position safety value. Under the current double-integrator Euler rollout, the next position is determined by the current velocity over one `dt`; the acceleration control changes the next velocity, but it does not directly change the immediate next position used by the GSplat position safety query. This explains why the current one-step acceleration correction cannot remove the immediate sampled-data margin violations and motivates either a multi-step predictive correction or a position-level safe-start/trajectory adjustment.
