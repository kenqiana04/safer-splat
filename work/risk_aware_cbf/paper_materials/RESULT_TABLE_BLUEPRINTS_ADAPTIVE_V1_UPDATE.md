# Result Table Blueprints: Adaptive V1 Update

## Table A: Adaptive V1 Closed-Loop Pilot Summary

Purpose: show that Adaptive V1 is integrated and stable in closed-loop pilots, without claiming efficiency improvement.

Columns:

- profile
- selected_K_mean
- selected_K_p95
- measured_candidate_count_mean
- runtime_mean
- collision_count
- qp_infeasible_count
- H1/H2/H3 margin violations
- DT_warning_count
- role / interpretation

Key numbers:

| profile | selected_K_mean | selected_K_p95 | measured_candidate_count_mean | runtime_mean | collision_count | qp_infeasible_count | H1/H2/H3 | DT_warning_count | interpretation |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- | ---: | --- |
| fixed | 2000.00 | 2000 | 23346.90 | 0.058599 | 0 | 0 | 93/98/103 | 101 | fixed V1 reference |
| adaptive_balanced | 1877.35 | 5600 | 23308.60 | 0.058390 | 0 | 0 | 93/98/103 | 101 | risk-responsive support module |

Takeaway: closed-loop integration and risk response are supported; candidate-count and runtime improvement are not supported.

Forbidden interpretation: do not claim runtime improvement or candidate-count reduction from this table.

## Table B: Targeted DT-Risk Window Analysis

Purpose: show that Adaptive V1 increases scheduled budget in risk windows but does not reduce measured candidate count.

Columns:

- profile
- risk_window selected_K_mean
- non_risk_window selected_K_mean
- measured_candidate_count_mean
- forced_candidate_fraction
- heading_fraction_final
- H1/H2/H3 violations
- interpretation

Key numbers:

| profile | risk_window selected_K_mean | non_risk_window selected_K_mean | risk_window measured_candidate_mean | forced_candidate_fraction | heading_fraction_final | H1/H2/H3 | interpretation |
| --- | ---: | ---: | ---: | ---: | ---: | --- | --- |
| fixed | 2000.00 | 2000.00 | 24920.31 | 1.00 | about 0.99 | 93/98/103 | fixed reference |
| adaptive_balanced | 5768.84 | 1483.19 | 24914.66 | 1.00 | 0.990847 | 93/98/103 | selected_K responds, final count unchanged |

Takeaway: risk-window selected_K ratio balanced/fixed is `2.884422`, but measured candidate-count ratio is `0.999773`.

Forbidden interpretation: do not call this an official benchmark or a candidate-count improvement result.

## Table C: Forced-Candidate Decomposition

Purpose: explain why `selected_K` did not control final candidate count.

Columns:

- scope
- selected_K_mean
- final_unique_mean
- heading_mean
- forced_near_mean
- history_mean
- forced_fraction_mean
- budget_limited_mean
- conclusion

Key numbers:

| scope | selected_K_mean | final_unique_mean | heading_mean | forced_near_mean | history_mean | forced_fraction_mean | budget_limited_mean | conclusion |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| targeted all_steps | 2746.67 | 24225.02 | 24148.18 | 160.43 | 52.48 | 1.00 | 0.00 | heading dominates |
| targeted risk_window | 5768.84 | 24914.66 | 24682.84 | 404.12 | 132.03 | 1.00 | 0.00 | forced union exceeds budget |
| targeted non_risk_window | 1483.19 | 23936.70 | 23924.65 | 58.55 | 19.22 | 1.00 | 0.00 | final set still forced-dominated |

Takeaway: final candidate count is controlled by forced heading candidates, not by the optional risk-ranked remainder.

Forbidden interpretation: do not say `selected_K_applied` means final candidate count was capped.

