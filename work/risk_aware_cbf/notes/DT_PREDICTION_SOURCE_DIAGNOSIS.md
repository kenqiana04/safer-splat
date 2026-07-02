# DT Prediction Source Diagnosis

Generated at: 2026-07-02T13:47:31

## Result

- prediction_type: `independent_dynamics_rollout`
- independent_rollout_available: `True`
- actual_next_source: `recorded_trajectory_next_row`
- same_field_used_for_prediction_and_actual: `False`
- checked_transitions: `14322`
- prediction_error_mean: `0.00018584718942260908`
- prediction_error_p95: `0.0006002016249112785`
- prediction_error_max: `0.004004968795925379`

## Interpretation

The V4-A audit recomputes the next state with `double_integrator_dynamics(x_t, u_t) * dt + x_t` and compares it with the next row recorded in `navigation_step_trajectory.csv`.

The predicted state and actual next state do not come from the same CSV fields. However, the recorded trajectory itself was produced by the same deterministic wrapper dynamics during simulation, so zero prediction error is expected.

Therefore the current audit is an independent dynamics replay against a simulated trajectory. It is not an external physical prediction audit.

The V4-B corrective runner uses the same independent one-step dynamics rollout before executing each control.
