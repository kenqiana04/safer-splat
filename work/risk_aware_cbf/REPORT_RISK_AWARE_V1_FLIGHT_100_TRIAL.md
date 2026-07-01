# Risk-Aware V1 Flight 100-Trial Report

## Scope

This report validates Risk-Aware V1 bestD on the flight 100-trial official checkpoint.
It does not modify the official SAFER-Splat baseline.
It does not claim a new CBF theorem.

## Scene Setup

- scene: flight
- checkpoint path: outputs/flight/splatfacto/2024-09-12_172434/config.yml
- gaussian_count: 281756
- active_frequency availability: unavailable; active_frequency was zero-filled for the risk score table
- risk score table: /disk1/zlab/projects/safer-splat/work/risk_aware_cbf/results/flight_risk_score_table_v0.csv

## Method

- method: risk_aware_v1_bestD
- candidate_budget: 2000
- near_distance_threshold: 0.05
- heading_distance_threshold: 0.25
- heading_cos_threshold: 0.5
- risk_score: risk_v2_hybrid
- actual insertion level: partial_pre_cbf
- SubsetGSplatLoader: reproduction-only wrapper
- official source modified: no

## Flight 100-Trial Comparison

| comparison_label | collision_count | collision_free_count | min_safety_h_min | progress_mean | intervention_rate_mean | control_deviation_mean | active_constraints_mean | runtime_mean | runtime_p95 | qp_infeasible_count | fallback_used_rate | candidate_count_final_mean |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| flight_no_filter | 96 | 4 | -0.000915397075 | 0.9879985532 | 0 | 0 | 0 | 2.322758536e-05 | 3.720740974e-05 | 0 |  |  |
| flight_safer_splat_filter | 1 | 99 | -0.0003094291314 | 0.4516750251 | 0.7858861937 | 0.06204425696 | 249.6304612 | 0.119267727 | 0.1334303422 | 0 |  |  |
| flight_risk_aware_v1_bestD | 1 | 99 | -0.0003094291314 | 0.4519552911 | 0.7568686172 | 0.0614900301 | 158.8149597 | 0.06199715268 | 0.069453653 | 0 | 0 | 16815.13486 |

## Cross-Scene Comparison

| comparison_label | collision_count | min_safety_h_min | progress_mean | active_constraints_mean | runtime_mean | runtime_p95 | qp_infeasible_count | fallback_used_rate | candidate_count_final_mean |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| flight_safer_splat_filter | 1 | -0.0003094291314 | 0.4516750251 | 249.6304612 | 0.119267727 | 0.1334303422 | 0 |  |  |
| flight_risk_aware_v1_bestD | 1 | -0.0003094291314 | 0.4519552911 | 158.8149597 | 0.06199715268 | 0.069453653 | 0 | 0 | 16815.13486 |
| stonehenge_safer_splat_filter | 0 | 0.0003172545403 | 0.3246967511 | 505.5866495 | 0.06307919365 | 0.07194588652 | 0 |  |  |
| stonehenge_risk_aware_v1_default | 0 | 0.0003172539582 | 0.3246946944 | 385.5619684 | 0.03987356792 | 0.04293182356 | 0 | 0 | 10809.80223 |
| stonehenge_risk_aware_v1_bestD | 0 | 0.0003172536672 | 0.3246745833 | 252.2219893 | 0.04044284326 | 0.04454808397 | 0 | 0 | 9905.290047 |

Cross-scene checks:

- both scenes preserve safety: False
- both scenes preserve progress: True
- both scenes reduce runtime: True
- bestD as cross-scene default: not yet; the flight trial-57 safety failure must be investigated first.

## Honest Interpretation

Flight 100-trial is not strictly collision-free: SAFER-Splat baseline and Risk-Aware V1 bestD both report one collision on trial 57. Therefore this run supports computational-efficiency improvement on flight, but it does not support a claim of cross-scene robustness yet.

Progress is preserved within the 1 percent rule, so the report should say progress preserved, not progress improved.

Runtime efficiency is improved: both runtime_mean and runtime_p95 for Risk-Aware V1 bestD are lower than the flight SAFER-Splat baseline. Active constraints are also lower.

Because active_frequency is unavailable for flight, the flight risk score uses static Gaussian attributes plus online distance/heading terms, with active_frequency zero-filled.

## Claim Boundary

The reported min_safety_h is not meter clearance.
This is still a wrapper-level prototype.
The method does not prove a new CBF theorem.
The method has been validated on stonehenge and flight, not all official scenes.

## Next Step Decision

TUNE_FLIGHT

Reason: flight 100-trial has a collision or non-positive min_safety_h, so cross-scene robustness should not be claimed yet.
