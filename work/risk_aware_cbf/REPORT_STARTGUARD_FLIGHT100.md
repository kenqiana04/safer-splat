# StartGuard Flight100 Report

## Scope

This report evaluates StartGuard on flight 100 trials.
It does not modify official SAFER-Splat source code.
It does not claim a new CBF theorem.

## Method

StartGuard first performs initial safety certification with the same GSplat safety query used by the CBF pipeline. Trials marked initial_near_unsafe or initial_unsafe are passed through safe-start repair before navigation. Post-repair navigation is then run with either V1 bestD candidate budgeting or the SAFER-Splat CBF filter. Official source was modified: no.

## Initial Safety Audit

total trials: 100
initial_safe count: 92
initial_near_unsafe count: 7
initial_unsafe count: 1
repair-needed count: 8

## Repair Statistics

repair_success_count: 8
repair_failure_count: 0
repair_distance_mean: 0.004999758638790424
repair_distance_p95: 0.013249031838096802
repair_distance_max: 0.014999072286579145
repair_steps_mean: 1.0
repair_steps_p95: 2.6499999999999995
repair_steps_max: 3.0

## Navigation Results

| method | collision_count | min_safety_h_min | progress_mean | runtime_mean | runtime_p95 | qp_infeasible_count | repair_used_count | repair_distance_mean |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| original flight safer_splat_filter | 1 | -0.0003094291314482689 | 0.4516750251372018 | 0.11926772699289204 | 0.13343034221045671 | 0 | 0 |  |
| original flight risk_aware_v1_bestD | 1 | -0.0003094291314482689 | 0.45195529113721056 | 0.06199715267959731 | 0.06945365300402044 | 0 | 0 |  |
| StartGuard + safer_splat_filter | 0 | 0.00019784539472311735 | 0.4517657412778257 | 0.10866290991479646 | 0.12067706932965666 | 0 | 8 | 0.004999758638790424 |
| StartGuard + risk_aware_v1_bestD | 0 | 0.00019784551113843918 | 0.45205064332574657 | 0.05795951384430193 | 0.06526291041448712 | 0 | 8 | 0.004999758638790424 |

## Honest Interpretation

StartGuard does not erase original initial safety violations.
For initial_unsafe / near_unsafe trials, original initial safety and post-repair navigation are reported separately.
StartGuard+V1 bestD achieves collision-free post-repair navigation in this flight100 validation, supporting StartGuard as an initial-condition repair module.
No repair failure or post-repair navigation failure was observed in this run.

## Claim Boundary

StartGuard is a pre-execution certification and repair module.
The reported min_safety_h is not meter clearance.
No official SAFER-Splat source code is modified.
No new CBF theorem is claimed.
Post-repair results are not the same as original benchmark results.

## Next Decision

WRITE_METHOD_AND_EXPERIMENT_SECTIONS
