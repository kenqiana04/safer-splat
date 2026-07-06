# Adaptive V1 Balanced Decision

## 1. Conservative Scheduler Problem

The conservative scheduler proved risk response but overused max-budget fallback in offline replay. This increased `selected_K_mean` and pushed `selected_K_p95` to the recovery budget.

## 2. Balanced Scheduler Result

Balanced reduces over-fallback: `True`.

Balanced reduces selected_K mean: `True`.

Balanced keeps H2/H3 warning response: `True` / `True`.

## 3. Three-Way Comparison

| profile | selected_K_mean | selected_K_p95 | selected_K_max | fallback_count | fallback_fraction | mode_nominal_count | mode_caution_count | mode_critical_count | mode_recovery_support_count | H2_warning_selected_K_mean | H2_warning_selected_K_p95 | H3_warning_selected_K_mean | H3_warning_selected_K_p95 | low_margin_selected_K_mean | low_margin_selected_K_p95 | non_warning_selected_K_mean | non_warning_selected_K_p95 | collision_count | qp_infeasible_count | H1_margin_violation_count | H2_margin_violation_count | H3_margin_violation_count |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| fixed | 2000 | 2000 | 2000 | 0 | 0 | 0 | 0 | 0 | 0 | 2000 | 2000 | 2000 | 2000 | 2000 | 2000 | 2000 | 2000 | 0 | 0 | 96 | 101 | 108 |
| adaptive_conservative | 2037.61 | 8000 | 8000 | 93 | 0.0529915 | 796 | 714 | 152 | 93 | 7603.96 | 8000 | 7370.37 | 8000 | 8000 | 8000 | 1687.92 | 4000 | 0 | 0 | 96 | 101 | 108 |
| adaptive_balanced | 2033.05 | 8000 | 8000 | 91 | 0.0518519 | 796 | 714 | 154 | 91 | 7603.96 | 8000 | 7370.37 | 8000 | 7913.98 | 8000 | 1683.06 | 4000 | 0 | 0 | 96 | 101 | 108 |

## 4. Continue Adaptive V1

Recommendation: `True`.

## 5. Closed-Loop Smoke

Recommendation: `True`. This is the next appropriate step before any closed-loop flight20 or full100 run.

## 6. Flight20 Closed-Loop

Recommendation now: `False`. Do closed-loop smoke first.

## 7. Full100 Now

Recommendation: `False`. Offline replay should not be used to jump directly to full100.

## 8. Paper Method Role

Use Adaptive V1 as an efficiency / risk-response support module or ablation until closed-loop evidence exists. Do not present it as a new safety proof.

## 9. Ablation Role

Balanced Adaptive V1 is suitable as an ablation candidate because it demonstrates controlled risk-responsive scheduling in offline replay.

## 10. Recommended Wording

- Adaptive V1 schedules candidate budget based on DT warnings and local risk signals.
- Balanced scheduling reduces over-fallback relative to the conservative profile in offline replay.
- DT Verification and full-query safety checks remain separate modules.

## 11. Forbidden Wording

- Do not claim Adaptive V1 alone guarantees safety.
- Do not claim a new CBF theorem.
- Do not describe margin violation as collision.
- Do not describe `min_safety_h` as meter clearance.
- Do not describe offline replay as closed-loop navigation.
- Do not call `selected_K` a measured closed-loop candidate count.
- Do not claim closed-loop runtime improvement from offline replay.
