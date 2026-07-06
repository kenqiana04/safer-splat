# Adaptive V1 Targeted DT-Risk Closed-Loop Decision

## Success

Continue Adaptive V1: `True`.

Target trials: `[7, 9, 12, 13, 14]`.

## Integration

Balanced selected_K_applied_rate: `1.0`.

Recovery used count balanced: `0`.

## Risk Response

Risk-window selected_K mean balanced: `5768.844221105528`.

Non-risk-window selected_K mean balanced: `1483.1932773109243`.

Adaptive balanced increases selected_K in risk windows: `True`.

## Candidate Dominance

Forced candidates still dominate: `True`.

Budget-limited candidate count zero: `True`.

Candidate count changed in risk windows: `False`.

Efficiency improvement evidence: `False`.

## Safety

Safety degradation detected: `False`.

Margin violation is not collision. `min_safety_h` is not metric clearance.

## Recommendations

- Full100 now: `False`
- Forced-candidate dominance follow-up: `True`
- Paper role: `support_module_or_ablation_not_main_safety_method`

## Recommended Wording

- Adaptive V1 balanced was tested on targeted DT-risk closed-loop trials.
- `selected_K` was passed into V1 candidate budgeting.
- Adaptive V1 responded to DT-risk windows by increasing the scheduled budget.
- Final candidate count remained dominated by forced candidates.

## Forbidden Wording

- Do not claim Adaptive V1 independently guarantees safety.
- Do not claim a new CBF theorem.
- Do not describe margin violation as collision.
- Do not describe targeted DT-risk as a full benchmark or official full100 result.
- Do not claim candidate-count or runtime improvement from this diagnostic.
