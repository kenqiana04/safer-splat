# FC-Aware V1 Targeted Extension Design

## Purpose

This task evaluates FC-Aware V1 `nearest_first + heading cap 16000` in targeted DT-risk / low-margin closed-loop windows. It is a targeted extension only, not flight20, not full100, not an official benchmark validation, and not a safety guarantee.

## Why Targeted Extension

The capped smoke verified wrapper-level cap integration and early closed-loop stability, but it did not fully cover the main targeted risk windows for trials 12 and 13. The next defensible step is to cover the real DT-risk / low-margin windows while retaining the fixed baseline comparison and staged stop rules.

## Profiles

- `fixed`: original V1 behavior without heading cap.
- `fc_aware_nearest_cap16000`: wrapper-level heading cap with deployable nearest-first ranking.

## Target Scopes

- Stage 1: trial 14, max_steps 80, target window 53:70.
- Stage 2: trial 12, max_steps 180, target window 96:167.
- Stage 3: trial 13, max_steps 190, target window 107:179.
- Optional Stage 4: trial 7, max_steps 140, target window 121:131.
- Optional Stage 5: trial 9, max_steps 130, target window 87:111.

## Safety Guard / Fallback

The wrapper keeps all near candidates, caps heading candidates by nearest-first top 16000, keeps history conservatively, and uses full heading fallback on missing fields or wrapper guard failure. DT Verification indicators are logged. The run stops if collision or QP infeasibility appears. No V4-C recovery is enabled.

## Metrics

Each analysis reports both `all_steps` and `risk_window` scopes:

- runtime mean / p95 / max,
- measured candidate count mean / p95 / max,
- heading before / after,
- final before / after,
- measured/final/heading candidate ratios,
- cap applied count,
- fallback count / reasons,
- collision count,
- QP infeasible count,
- min_safety_h minimum and delta,
- H1/H2/H3 margin violation counts and deltas,
- DT warning and low-margin deltas,
- progress mean / delta,
- recovery_used_count.

## Pass / Fail Criteria

Pass requires no crash, no collision, no QP infeasible event, no min_h degradation beyond tolerance, no H1/H2/H3 violation increase, no DT-warning increase, observed candidate-count reduction, non-excessive fallback, and recovery_used_count = 0.

Fail and stop if any collision, QP infeasibility, H-step margin worsening, meaningful min_h worsening, no final candidate reduction, or full-heading fallback being used so often that the cap is not effectively active.
