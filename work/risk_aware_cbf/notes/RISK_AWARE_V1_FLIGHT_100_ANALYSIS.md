# Risk-Aware V1 Flight 100-Trial Analysis

Generated: 2026-07-01T14:57:32

## Inputs

- flight 100 result dir: `/disk1/zlab/projects/safer-splat/work/risk_aware_cbf/results/risk_aware_v1_pre_cbf_flight_100_bestD`
- flight 20 bestD dir: `/disk1/zlab/projects/safer-splat/work/risk_aware_cbf/results/risk_aware_v1_pre_cbf_flight_20_bestD`
- flight 20 default dir: `/disk1/zlab/projects/safer-splat/work/risk_aware_cbf/results/risk_aware_v1_pre_cbf_flight_20_default`
- stonehenge 100 default dir: `/disk1/zlab/projects/safer-splat/work/risk_aware_cbf/results/risk_aware_v1_pre_cbf_stonehenge_100`
- stonehenge 100 bestD dir: `/disk1/zlab/projects/safer-splat/work/risk_aware_cbf/results/risk_aware_v1_pre_cbf_stonehenge_100_bestD`

## Flight 100 Comparison

| comparison_label | collision_count | collision_free_count | min_safety_h_min | progress_mean | intervention_rate_mean | control_deviation_mean | active_constraints_mean | runtime_mean | runtime_p95 | qp_infeasible_count | fallback_used_rate | candidate_count_final_mean |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| flight_no_filter | 96 | 4 | -0.000915397075 | 0.9879985532 | 0 | 0 | 0 | 2.322758536e-05 | 3.720740974e-05 | 0 |  |  |
| flight_safer_splat_filter | 1 | 99 | -0.0003094291314 | 0.4516750251 | 0.7858861937 | 0.06204425696 | 249.6304612 | 0.119267727 | 0.1334303422 | 0 |  |  |
| flight_risk_aware_v1_bestD | 1 | 99 | -0.0003094291314 | 0.4519552911 | 0.7568686172 | 0.0614900301 | 158.8149597 | 0.06199715268 | 0.069453653 | 0 | 0 | 16815.13486 |

## Required Safety And Stability Checks

- flight V1 bestD collision_count is 0: False
- flight V1 bestD min_safety_h_min > 0: False
- flight V1 bestD qp_infeasible_count is 0: True
- flight V1 bestD fallback_used_rate is low: True
- flight V1 bestD runtime_mean lower than baseline: True
- flight V1 bestD runtime_p95 lower than baseline: True
- flight V1 bestD active_constraints_mean lower than baseline: True
- flight V1 bestD progress preserved within 1 percent: True
- flight baseline collision trials: [57]
- flight V1 bestD collision trials: [57]

## Cross-Scene Comparison

| comparison_label | collision_count | min_safety_h_min | progress_mean | active_constraints_mean | runtime_mean | runtime_p95 | qp_infeasible_count | fallback_used_rate | candidate_count_final_mean |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| flight_safer_splat_filter | 1 | -0.0003094291314 | 0.4516750251 | 249.6304612 | 0.119267727 | 0.1334303422 | 0 |  |  |
| flight_risk_aware_v1_bestD | 1 | -0.0003094291314 | 0.4519552911 | 158.8149597 | 0.06199715268 | 0.069453653 | 0 | 0 | 16815.13486 |
| stonehenge_safer_splat_filter | 0 | 0.0003172545403 | 0.3246967511 | 505.5866495 | 0.06307919365 | 0.07194588652 | 0 |  |  |
| stonehenge_risk_aware_v1_default | 0 | 0.0003172539582 | 0.3246946944 | 385.5619684 | 0.03987356792 | 0.04293182356 | 0 | 0 | 10809.80223 |
| stonehenge_risk_aware_v1_bestD | 0 | 0.0003172536672 | 0.3246745833 | 252.2219893 | 0.04044284326 | 0.04454808397 | 0 | 0 | 9905.290047 |

## Interpretation

- safety preserved across stonehenge and flight: False
- progress preserved across stonehenge and flight: True
- runtime improved across stonehenge and flight: True
- preferred config: risk_aware_v1_bestD remains the computationally preferred V1 setting, but it is not ready as the default safety setting until the flight trial-57 collision is addressed.
- recommended decision: TUNE_FLIGHT

The flight 100-trial result shows strong runtime and active-constraint reductions, but it does not pass the strict safety gate because trial 57 has negative min_safety_h for both SAFER-Splat baseline and V1 bestD. This should be treated as an important experiment finding, not manually corrected.
