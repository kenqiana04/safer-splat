# Adaptive V1 Closed-Loop Smoke Design

## Purpose

This smoke test only checks whether `adaptive_balanced` can be connected to the real closed-loop navigation / CBF filtering pipeline. It is not a full benchmark, not a flight20 closed-loop study, and not a full100 result.

## Difference From Offline Replay

Offline replay used saved V4-A + V1 trajectory rows. In that setting, `selected_K` was a scheduled budget proxy, and runtime, collision, QP infeasibility, and H-step margin violations were inherited from the saved trajectory.

Closed-loop smoke runs the navigation loop. The scheduler is called before each CBF-QP solve, and `selected_K` is written into the V1 candidate selector before candidate selection and CBF matrix construction. Therefore `selected_K_applied=True` means the scheduled budget was actually passed to candidate budgeting for that step.

The scheduler DT warning signal is computed from a pre-control nominal repeated-control preview. The reported H=1/H=2/H=3 margin values are computed after the CBF-QP using the executed filtered control. This keeps the scheduler causal while still reporting executed sampled-data margin behavior.

## Smoke Test Scope

The staged smoke sequence is:

1. Trial 0, `max_steps=5`.
2. Trial 0, `max_steps=20`.
3. Hotspot trial 12, `max_steps=20`; trial 85 can be used if trial 12 is unavailable.

The smoke should stop before broader closed-loop experiments if there is a crash, candidate budget is not actually applied, recovery is unexpectedly used, collision appears, QP infeasibility appears, or runtime becomes clearly abnormal.

## Compared Profiles

The required comparison is:

- fixed V1.
- adaptive_balanced.

`adaptive_conservative` can be added later, but this smoke focuses on whether balanced scheduling can enter the closed-loop V1 pipeline.

## Recovery Setting

V4-C recovery is disabled by default. This smoke tests Adaptive V1 candidate budgeting inside the CBF filtering pipeline. Predictive Recovery would confound the interpretation and should remain a separate follow-up experiment.

## Metrics

The smoke records:

- `runtime_mean`
- `runtime_p95`
- `runtime_max`
- `selected_K_mean`
- `selected_K_p95`
- `selected_K_max`
- `selected_K_applied_rate`
- `measured_candidate_count_mean`
- `measured_candidate_count_p95`
- `active_constraint_count_mean`
- `active_constraint_count_p95`
- `qp_infeasible_count`
- `collision_count`
- `min_safety_h_min`
- `progress_mean`
- `H1_margin_violation_count`
- `H2_margin_violation_count`
- `H3_margin_violation_count`
- mode counts
- `fallback_count`
- `fallback_fraction`
- DT-warning `selected_K_mean`
- non-warning `selected_K_mean`

## Pass / Fail Criteria

Pass if:

- No crash.
- No forbidden source modification.
- `selected_K_applied=True` for scheduled steps.
- `recovery_used=False`.
- `collision_count=0`.
- QP infeasibility does not appear.
- Runtime is not clearly abnormal.
- Required fields are present.

Hold if:

- The runner cannot pass `selected_K` into candidate selection.
- `selected_K_applied` is false or missing.
- Collision appears.
- QP infeasibility appears.
- Runtime becomes clearly abnormal.
- Required fields are missing.

## Reporting Constraints

The report must state:

- Closed-loop smoke is not a full benchmark.
- Smoke is not an official flight100 result.
- Adaptive V1 does not independently guarantee safety.
- `min_safety_h` is the repository GSplat ellipsoid safety h value, not meter clearance.
- Margin violation is not collision.
- No official SAFER-Splat core source is modified.
- No new CBF theorem is claimed.
- V4-C recovery is disabled unless explicitly stated otherwise.
