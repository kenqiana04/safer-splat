# StartGuard Trial 57 Report

## Scope

This report evaluates StartGuard for the flight trial-57 initial-unsafe hard case.
It does not modify official SAFER-Splat source code.
It does not claim a new CBF theorem.

## Initial Safety Certification

original trial 57 start: (-0.05220765975846667, -0.11486672717071932, -0.07993204035098048)
original initial_min_safety_h: -0.0003094291314482689
initial safety status: initial_unsafe
nearest / most violated Gaussian: 218853

## Safe-Start Repair

repair_success: True
repaired start: (-0.06253296136856079, -0.1133786290884018, -0.06915494054555893)
repaired_min_safety_h: 0.000642147846519947
repair_distance: 0.014999072286579145
repair_steps: 3
safety_margin: 0.0005
failure_reason: 

## Post-Repair Navigation

| method | collision_count | min_safety_h_min | progress_mean | runtime_mean | runtime_p95 | qp_infeasible_count | repair_distance | repair_steps |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| safer_splat_filter original trial57 | 1 | -0.0003094291314482689 | 0.5209763611652722 | 0.1151152839479239 | 0.14971557017415763 | 0 |  |  |
| risk_aware_v1_bestD original trial57 | 1 | -0.0003094291314482689 | 0.5226823949556479 | 0.05252950557548067 | 0.05853408668190241 | 0 |  |  |
| safer_splat_filter_post_repair | 0 | 0.000642147846519947 | 0.5251198425175745 | 0.11134652208591647 | 0.12758519453927875 | 0 | 0.014999072286579145 | 3 |
| risk_aware_v1_bestD_post_repair | 0 | 0.000642147846519947 | 0.5263694109741218 | 0.05505041135748958 | 0.07247145380824804 | 0 | 0.014999072286579145 | 3 |

## Honest Interpretation

If StartGuard repairs trial57, this does not mean the original initial state was safe. It means StartGuard detects an initial safety violation and computes a nearby safe start before task execution.
If post-repair navigation is collision-free, this supports StartGuard as an initial-condition repair module for 3DGS-CBF navigation.
If repair distance is large, the cost is reported directly and no minimal-perturbation claim is made.
If repair fails, StartGuard should not be claimed to solve trial57.

## Claim Boundary

StartGuard is a pre-execution certification and repair module.
The original benchmark trial remains initially unsafe.
Post-repair results are reported separately from original-trial results.
The reported min_safety_h is not meter clearance.
No official SAFER-Splat source code is modified.
No new CBF theorem is claimed.

## Next Decision

PROCEED_TO_STARTGUARD_FLIGHT100
