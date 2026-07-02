# V4-B Corrective Discrete-Time Safety Filter Report

## Scope

This report evaluates V4-B: corrective discrete-time safety filtering. It does not modify official SAFER-Splat source code. It does not claim a new CBF theorem.

## Method

V4-B extends the FAS-CBF framework after V4-A. It uses one-step rollout verification, local control candidate sampling, full-query safety checks, and a correction selection rule around Risk-Aware V1 bestD / SAFER-Splat CBF-QP outputs.

## DT Prediction Source Diagnosis

- prediction_type: `independent_dynamics_rollout`
- independent_rollout_available: `True`
- limitation: the recorded trajectory is simulated by the same deterministic wrapper dynamics, so zero prediction error is expected. This is not an external physical prediction audit.

## Results

|section|num_steps|base_margin_violation_count|exec_margin_violation_count|collision_count|qp_infeasible_count|progress_mean|runtime_mean|runtime_p95|correction_used_count|correction_success_count|correction_failed_count|control_delta_mean|
|---|---|---|---|---|---|---|---|---|---|---|---|---|
|v4a_audit_repair_needed|1183|21|21||||||||||
|v4b_repair_needed|1197|15|15|0|0|0.5502362844303678|0.06920030725147278|0.2458211361197755|15|0|15|0.00046338405295768203|
|v4a_audit_flight20|1735|93|93||||||||||


## Correction Failure Analysis

- repair-needed correction rows: `15`
- h_improvement_mean: `0.0`
- h_improvement_max: `0.0`
- selected_candidate_sources: `{'scaled_base_0': 15}`

In the tested one-step wrapper, candidate controls did not improve the immediate next-step position safety value. This is consistent with the current double-integrator Euler rollout: the acceleration control changes velocity first, while the queried next position over one `dt` is determined by the current velocity. Therefore one-step acceleration-only correction is structurally unable to fix immediate position-margin violations in this setup.

## Honest Interpretation

If `exec_margin_violation_count` decreases, V4-B reduces sampled-data margin violations in the tested runs. If it does not decrease, the current candidate sampling strategy is insufficient. Runtime overhead and progress changes are reported as trade-offs. Margin violations are not collisions; collision-free and margin-satisfying behavior are reported separately.

## Claim Boundary

- No official SAFER-Splat source code is modified.
- No new CBF theorem is claimed.
- `min_safety_h` is not meter clearance.
- V4-B provides empirical one-step sampled-data correction unless formal assumptions are later proved.
- Post-repair navigation is not original benchmark navigation.

## Next Decision

Recommended decision: `PROCEED_TO_HSTEP_PREDICTIVE_RECOVERY`.
