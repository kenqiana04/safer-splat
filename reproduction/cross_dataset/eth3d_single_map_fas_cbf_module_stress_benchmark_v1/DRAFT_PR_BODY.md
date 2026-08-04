## Scope

This task deliberately recenters ETH3D from deployment-level map qualification to a bounded local-safety controller stress carrier. It preserves PR #79 and its planner-coupled Case C result unchanged.

## Frozen map and execution boundary

- Official graphdeco 3DGS source: `54c035f7834b564019656c3e3fcc3646292f727d`
- Dataset / scene / split / frontend / formal seed / formal map: exactly one each
- Formal training: one 30K attempt, seed `20260804`, normal exit, no resume
- Formal map PLY SHA-256: `927734a2339a3f2710640065b0893eaae162cc0144ac67e2f377bcff2e71ae34`
- Canonical export: three identical fresh trees, no filtering or map mutation
- Training reference, held-out, and GT-depth reads: zero

## Controller benchmark

The method-independent registry contains 100 frozen scenarios: 20 in each of G0-G4. Five cumulative methods were run on every scenario, yielding 500/500 terminal paired records with no infrastructure failures and no reference-oracle controller input.

| Method | Success | QP infeasible | Start rejected | Reference collisions |
|---|---:|---:|---:|---:|
| M0 SAFER | 20 | 80 | 0 | 0 |
| M1 + Start-Safe | 20 | 60 | 20 | 0 |
| M2 + Feasibility-Aware | 20 | 60 | 20 | 0 |
| M3 + DT Verification | 20 | 60 | 20 | 0 |
| M4 Full FAS-CBF | 20 | 60 | 20 | 0 |

Start-Safe activated 14 times but did not support the preregistered advantage hypothesis. Feasibility-aware selection, discrete-time verification, and predictive recovery did not activate under this registry. Smoothness results are diagnostic only; no smooth-control or adaptive-margin claim is made.

## Decision

- `FINAL_STATUS=PASS_ETH3D_MAP_WITH_INSUFFICIENT_FAS_CBF_STRESS_ACTIVATION`
- `FINAL_DECISION=REPAIR_METHOD_INDEPENDENT_STRESS_SCENARIO_GENERATOR`
- `ONLY_NEXT_TASK=REFINE_FAS_CBF_STRESS_SCENARIO_ACTIVATION_ON_FROZEN_ETH3D_MAP_V1`

The learned map passed the catastrophic minimum controller-viability gate, but this benchmark does not establish FAS-CBF superiority over SAFER. The next task must refine scenario activation on the same frozen map; it must not train another map or switch datasets.

## Validation and artifacts

- Final validator: `PASS_FINAL_BENCHMARK_VALIDATION`
- 100 scenarios, 5 methods, 500 compact per-run records, 25 figures
- Compact evidence only is committed; no dataset archives, environments, source snapshot, checkpoints, map arrays, dense renders, trajectories, credentials, or large logs are included
