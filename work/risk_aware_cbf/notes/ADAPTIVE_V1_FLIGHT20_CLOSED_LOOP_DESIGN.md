# Adaptive V1 Flight20 Closed-Loop Design

## 1. Purpose

This experiment runs an Adaptive V1 balanced flight20 closed-loop pilot on trials 0-19. It is not a full100 benchmark and not an official benchmark result.

## 2. Difference From Smoke

The closed-loop smoke only verified integration on short scopes. This flight20 pilot checks a longer trial set for closed-loop stability, runtime, QP behavior, collision status, H-step DT margins, mode switching, and whether scheduled budgets actually enter V1 candidate selection.

The result still cannot be treated as a full100 result.

## 3. Compared Profiles

The required comparison is:

- fixed V1 candidate budget
- adaptive_balanced V1 candidate budget

The conservative profile is not part of the default flight20 closed-loop pilot to keep scope controlled.

## 4. Recovery Setting

V4-C recovery is disabled. This isolates Adaptive V1 candidate budgeting from the optional predictive recovery module. Predictive Recovery remains an independent optional module and is not evaluated here.

## 5. Trial Scope And Resume

The runner supports trials 0-19 through `--trial-start 0 --trial-end 19`, plus explicit `--trials` or `--trial-id` for targeted reruns. With `--resume --skip-existing`, existing completed trial rows are loaded and skipped.

## 6. Metrics

The runner records step-level and trial-level metrics including runtime mean/p95/max, selected_K mean/p95/max, selected_K_applied_rate, measured_candidate_count mean/p95/max, active constraint counts, QP infeasible count, collision count, min_safety_h_min, progress, H1/H2/H3 margin violations, mode counts, fallback count/fraction, DT-warning counts, low-margin counts, recovery_used_count, crash_count, and missing_field_count.

## 7. Candidate Decomposition

Because the smoke run showed measured candidate count can remain dominated by forced candidates, the flight20 runner recomputes wrapper-visible candidate groups without modifying core code:

- selected_K
- applied_candidate_budget
- measured_candidate_count
- forced_near_candidate_count
- heading_candidate_count
- history_candidate_count
- forced_unique_candidate_count
- final_unique_candidate_count
- budget_limited_candidate_count
- forced_candidate_fraction

If a field cannot be obtained, the step row records `missing_field_flags`. The report must not guess unavailable decomposition.

## 8. Pass / Hold Criteria

Pass requires no crash, selected_K_applied_rate equal to 1.0, recovery_used_count equal to 0, collision_count equal to 0, no QP infeasibility increase, no abnormal runtime blow-up, no obvious min_safety_h degradation, no H1/H2/H3 margin violation degradation, and no core missing fields affecting the integration judgment.

Hold if selected_K is not applied, recovery is unexpectedly used, any crash or collision appears, QP infeasibility clearly increases, runtime becomes abnormal, or missing fields prevent judging the candidate-budget integration.

## 9. Reporting Constraints

The report must state that flight20 is not a full100 benchmark, Adaptive V1 does not independently guarantee safety, `min_safety_h` is the repository GSplat ellipsoid safety h value rather than metric clearance, margin violation is not collision, no official SAFER-Splat core source was modified, no new CBF theorem is claimed, and V4-C recovery was disabled.
