# MPC-style Recovery Targeted Pilot Decision

## Status

Sequence library sanity check: passed.

Evaluator status: completed dry-run, smoke H2_N64, targeted H2_N64, and targeted H3_N64.

Execution mode: offline trigger-state evaluator. This is not closed-loop recovery and not full100.

Official core source changes: none.

## Trigger Source

The evaluator reads:

`work/risk_aware_cbf/results/adaptive_v1_targeted_dt_risk_closed_loop/balanced/adaptive_v1_targeted_dt_risk_closed_loop_steps.csv`

Target windows select 199 rows across trials 7, 9, 12, 13, and 14.

## Profiles

| profile | horizon | sequence count | dt margin |
|---|---:|---:|---:|
| `primitive_h2_n64` | 2 | 64 | 0.0005 |
| `primitive_h3_n64` | 3 | 64 | 0.0005 |

Sequence families include nominal hold, deceleration, lateral, vertical, brake+lateral, brake+vertical, goal-preserving bias, previous-safe-action smoothing, and random shooting around the base action.

## H2_N64 Result

| metric | value |
|---|---:|
| trigger_count | 199 |
| success_count | 103 |
| improved_but_unresolved_count | 0 |
| no_improvement_count | 96 |
| failed_count | 0 |
| base_margin_violation_count | 101 |
| selected_exec_margin_violation_count | 96 |
| min_base_horizon_h | 0.000312344986 |
| min_exec_horizon_h | 0.000312344986 |
| h_improvement_mean | 1.39534e-07 |
| h_improvement_p95 | 4.71063e-07 |
| runtime_mean | 2.3606 |
| runtime_p95 | 2.43675 |
| runtime_max | 2.64463 |

Dominant selected types: `nominal_hold` 124, `smooth_previous_nominal` 60, `deceleration_0.5` 8, `previous_safe_hold` 3.

## H3_N64 Result

| metric | value |
|---|---:|
| trigger_count | 199 |
| success_count | 103 |
| improved_but_unresolved_count | 0 |
| no_improvement_count | 96 |
| failed_count | 0 |
| base_margin_violation_count | 108 |
| selected_exec_margin_violation_count | 96 |
| min_base_horizon_h | 0.000298623345 |
| min_exec_horizon_h | 0.000298623345 |
| h_improvement_mean | 8.50932e-07 |
| h_improvement_p95 | 3.22027e-06 |
| runtime_mean | 3.3939 |
| runtime_p95 | 3.48916 |
| runtime_max | 3.78611 |

Dominant selected types: `nominal_hold` 121, `smooth_previous_nominal` 54, `deceleration_0.5` 8, `deceleration_0.25` 6, `previous_safe_hold` 4.

## Taxonomy Interpretation

Both profiles have the same taxonomy:

- success: 103
- improved_but_unresolved: 0
- no_improvement: 96
- failed: 0

The unresolved cases are concentrated in trials 12, 13, and 14. H3 increases h improvement statistics but does not reduce the selected H-step margin violation count.

## Runtime

Runtime is controlled in the sense that the runs completed reliably, but it is not competitive with the existing V4-C references:

- H2_N64 offline mean: 2.3606 s per trigger
- H3_N64 offline mean: 3.3939 s per trigger
- V4-C R4_H2_N64 closed-loop reference mean: 0.095952 s
- V4-C H3_N128 closed-loop reference mean: 0.170388 s

Because modes differ, this is qualitative positioning only, not a direct runtime benchmark.

## R4_H2_N64 Comparison

Direct comparison is not available. The MPC-style pilot evaluates saved targeted trigger states offline. R4_H2_N64 evidence is existing closed-loop full100 / hotspot evidence.

Do not claim this pilot is better than R4_H2_N64.

## Decision

Continue this exact primitive H2_N64/H3_N64 MPC-style profile? No.

Recommend closed-loop smoke now? No for this exact profile. A closed-loop smoke would only be justified after a stronger sequence family or selection objective reduces the offline selected violation count.

Recommend flight20? No.

Recommend full100 now? No.

Recommend inclusion as paper main method? No.

Recommended positioning: optional recovery extension / future work. The pilot is useful as negative evidence that naive primitive-sequence MPC-style recovery does not outperform the existing V4-C direction on targeted DT-risk states.

## Safe Paper Wording

Safe:

- "We implemented a primitive-sequence, sampling-based MPC-style recovery evaluator as a targeted offline pilot."
- "The pilot is triggered by DT-risk states and evaluates short H-step recovery sequences."
- "In this targeted offline replay, the primitive H2/H3 N64 profiles did not eliminate all selected H-step margin violations."
- "The result supports keeping MPC-style recovery as optional future work unless stronger sequence optimization is added."

Forbidden:

- Do not call this full nonlinear MPC.
- Do not call this a closed-loop safety result.
- Do not claim a new CBF theorem.
- Do not claim standalone safety guarantees.
- Do not claim margin violation is collision.
- Do not claim `h` is meter clearance.
- Do not claim improvement over R4_H2_N64.
- Do not recommend full100 for the current primitive profile.
