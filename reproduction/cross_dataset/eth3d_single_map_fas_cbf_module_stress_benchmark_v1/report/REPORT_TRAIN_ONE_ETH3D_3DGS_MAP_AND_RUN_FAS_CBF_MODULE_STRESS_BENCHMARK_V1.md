# Train One ETH3D 3DGS Map and Run FAS-CBF Module Stress Benchmark V1

**PASS_ETH3D_MAP_WITH_INSUFFICIENT_FAS_CBF_STRESS_ACTIVATION**

ETH3D remains a local-safety controller stress carrier; PR #79 remains the authoritative planner-coupled negative result.

## 1. Branch

`eth3d-single-map-fas-cbf-module-stress-benchmark-v1`.

## 2. Draft PR

One Draft PR is created during Git handoff; no earlier PR is modified.

## 3. Commit

The result commit is the commit containing this report; see the PR head.

## 4. Base/head

Base `4694a7cbfa062a53ac270c1c1c5654a2d1b5f166`; task branch before result commit.

## 5. PR #79 preserved

PR #79 remains Open Draft and its planner-coupled Case C is not overturned.

## 6. Frozen identities

Protocol `a0a02fd284c75c600095510899e2878f198d69ff088b66eccd3313275fdbde7e`; split `dc6729a60e0f2971cb671e30bcce3a04adcd8f99298395d42f21855d666cc435`; TRAIN tree `5b0002cbdd4dff8985574c8f5d61640e9535709634959327e3b705794830b478`; reference mesh `82a9b20c9f3c7dc933f86c45e0855adf649fcf08b7549baba760cf385d489370`.

## 7. Official source

graphdeco commit `54c035f7834b564019656c3e3fcc3646292f727d`, tree `3e76b1a6180966faccc4c1cdf1bf95a68350c48f`, clean and immutable.

## 8. Environment

`PASS_OFFICIAL_3DGS_ENVIRONMENT_FUNCTIONAL`; Python 3.10.20; torch 2.1.2+cu118; CUDA 11.8; NVIDIA GeForce RTX 4090.

## 9. Compatibility patches

Task environment only: setuptools 82 to cached 80.9.0 for pkg_resources; three official CUDA submodules compiled into task-local wheels. Training semantics unchanged.

## 10. Smoke

500 iterations, loss 0.125699, 40092 Gaussians, `PASS_OFFICIAL_3DGS_500_ITERATION_SMOKE`.

## 11. Formal attempt

Exactly one formal attempt, seed 20260804, 30,000 iterations, no resume.

## 12. Training runtime

701.989 seconds; peak GPU 4338 MiB.

## 13. Final Gaussian count

664,873.

## 14. Checkpoint/map SHA

Checkpoint `de767580cb0a92ebfce90531bf77d4882f992091e927591d6e829b39009dfcf0`; PLY `927734a2339a3f2710640065b0893eaae162cc0144ac67e2f377bcff2e71ae34`.

## 15. Canonical export

Three fresh exports agree; canonical tree `06c1ff17d2ed5eb184b6a9699a3a32da431a1460840431a3effe76d5f03b9ee3`; no filtering/pruning.

## 16. TRAIN reference access

Reference, held-out, and GT-depth access during TRAIN are all zero.

## 17. Minimum viability

`PASS_ETH3D_SINGLE_MAP_MINIMUM_CONTROLLER_VIABILITY` with all 13 hard gates true; formal map SHA unchanged.

## 18. Heldout diagnostics

12 views, PSNR mean 10.6400 dB, SSIM mean 0.4436; descriptive only.

## 19. SAFER query/G0

2,000 deterministic nearest candidates; h/gradient/Hessian finite; runtime 0.017076 s.

## 20. Scenario registry

100 method-independent scenarios; SHA `9f9fce4d1875b57e7a55c3a9cbf5b5a0c3f8476d84b3deb53c920d9b6322bb1d`.

## 21. Group counts

{"G0_SAFE_CONTROL": 20, "G1_START_SAFE_BOUNDARY": 20, "G2_FEASIBILITY_DENSE": 20, "G3_SAMPLED_DATA_GAP": 20, "G4_PREDICTIVE_RECOVERY": 20}

## 22. Module activation

{"H1_START_SAFE": 14, "H2_FEASIBILITY_AWARE": 0, "H3_DISCRETE_TIME": 0, "H4_PREDICTIVE_RECOVERY": 0}

## 23. Methods completed

All five methods completed 100 terminal paired runs each.

## 24. Formal paired run count

500/500; state `COMPLETED`.

## 25. Collision by method/group

- G0_SAFE_CONTROL: M0=0, M1=0, M2=0, M3=0, M4=0
- G1_START_SAFE_BOUNDARY: M0=0, M1=0, M2=0, M3=0, M4=0
- G2_FEASIBILITY_DENSE: M0=0, M1=0, M2=0, M3=0, M4=0
- G3_SAMPLED_DATA_GAP: M0=0, M1=0, M2=0, M3=0, M4=0
- G4_PREDICTIVE_RECOVERY: M0=0, M1=0, M2=0, M3=0, M4=0

## 26. Progress, feasibility, constraints, runtime

- M0_SAFER_BASELINE: collisions=0, completions=20, progress_mean=0.023331 m, qp_infeasible=80, active_constraints_mean=2000.000, runtime_mean=0.005407 s
- M1_FAS_START_SAFE_ONLY: collisions=0, completions=20, progress_mean=0.022630 m, qp_infeasible=60, active_constraints_mean=1600.000, runtime_mean=0.023744 s
- M2_FAS_START_SAFE_PLUS_FEASIBILITY_AWARE: collisions=0, completions=20, progress_mean=0.022630 m, qp_infeasible=60, active_constraints_mean=160.041, runtime_mean=0.022771 s
- M3_FAS_PLUS_DISCRETE_TIME_VERIFICATION: collisions=0, completions=20, progress_mean=0.022630 m, qp_infeasible=60, active_constraints_mean=160.041, runtime_mean=0.035236 s
- M4_FULL_FAS_CBF: collisions=0, completions=20, progress_mean=0.022630 m, qp_infeasible=60, active_constraints_mean=160.041, runtime_mean=0.041868 s

## 27. QP infeasible

See per-method and per-group summaries; every terminal scientific failure is retained.

## 28. Active constraints

Feasibility-aware exact dominance removal uses unchanged control bounds and no hidden relaxation.

## 29. Runtime

Per-step mean/p95/max and component timings are retained per run.

## 30. Start-Safe evidence

- H1_START_SAFE: NOT_SUPPORTED (activation=14, primary_effect=-0, collision_delta=0)

## 31. Feasibility-Aware evidence

- H2_FEASIBILITY_AWARE: INACTIVE (activation=0, primary_effect=-0, collision_delta=0)

## 32. DT verifier evidence

- H3_DISCRETE_TIME: INACTIVE (activation=0, primary_effect=0, collision_delta=0)

## 33. Predictive Recovery evidence

- H4_PREDICTIVE_RECOVERY: INACTIVE (activation=0, primary_effect=-0, collision_delta=0)

## 34. Full FAS vs SAFER

- H5_FULL: NOT_SUPPORTED (activation=14, primary_effect=-0, collision_delta=0)

## 35. Module evidence matrix

- H1_START_SAFE: NOT_SUPPORTED (activation=14, primary_effect=-0, collision_delta=0)
- H2_FEASIBILITY_AWARE: INACTIVE (activation=0, primary_effect=-0, collision_delta=0)
- H3_DISCRETE_TIME: INACTIVE (activation=0, primary_effect=0, collision_delta=0)
- H4_PREDICTIVE_RECOVERY: INACTIVE (activation=0, primary_effect=-0, collision_delta=0)
- H5_FULL: NOT_SUPPORTED (activation=14, primary_effect=-0, collision_delta=0)

## 36. Smoothness diagnostics

`PASS_SMOOTHNESS_DIAGNOSTICS_RECORDED`; TV, jerk, intervention, and active-set switching are diagnostic only.

## 37. Regressions/failures

Failure registry contains 0 preserved paired cases; collision regression=False.

## 38. Execution counts

{"adaptive_margin_training_count": 0, "canonical_export_count": 3, "checkpoint_resume_count": 0, "compatibility_patch_count": 1, "controller_formal_run_count": 500, "controller_smoke_run_count": 50, "controller_tuning_after_smoke_count": 0, "dataset_count": 1, "formal_map_count": 1, "formal_seed_count": 1, "formal_training_attempt_count": 1, "frame_deletion_count": 0, "frontend_count": 1, "gt_depth_access_during_train": 0, "icp_sim3_count": 0, "map_filtering_count": 0, "map_mutation_count": 0, "mapper_sweep_count": 0, "mapping_baseline_count": 0, "operational_autonomy_action_count": 8, "per_method_formal_runs": {"M0_SAFER_BASELINE": 100, "M1_FAS_START_SAFE_ONLY": 100, "M2_FAS_START_SAFE_PLUS_FEASIBILITY_AWARE": 100, "M3_FAS_PLUS_DISCRETE_TIME_VERIFICATION": 100, "M4_FULL_FAS_CBF": 100}, "reference_access_during_train": 0, "scale_repair_count": 0, "scenario_count": 100, "scenario_deletion_after_results_count": 0, "scenario_group_counts": {"G0_SAFE_CONTROL": 20, "G1_START_SAFE_BOUNDARY": 20, "G2_FEASIBILITY_DENSE": 20, "G3_SAMPLED_DATA_GAP": 20, "G4_PREDICTIVE_RECOVERY": 20}, "scene_count": 1, "smoke_training_count": 1, "smoothness_tuning_count": 0, "source_clone_fetch_count": 1, "ssh_repair_count": 1, "task_local_environment_create_count": 1, "task_owned_process_cleanup_count": 3}

## 39. GPU final

GPU 1 task-owned compute clean=True.

## 40. Watchdog/SSH final

watchdog=RUNNING_SCHEDULED_TASK_LAST_RESULT_0x41301; managed reverse proxy=PASS_LOOPBACK_ONLY_HTTP_200_TUNNEL_ACTIVE; unrelated SSH preserved.

## 41. Operational autonomy

Only task-local proxy recovery, source acquisition, environment compatibility, adapter/probe fixes, and task-owned process cleanup were used; actions are recorded.

## 42. FINAL_STATUS

`PASS_ETH3D_MAP_WITH_INSUFFICIENT_FAS_CBF_STRESS_ACTIVATION`

## 43. FINAL_DECISION

`REPAIR_METHOD_INDEPENDENT_STRESS_SCENARIO_GENERATOR`

## 44. Unresolved evidence

Held-out image metrics remain descriptive; no deployment/N3/global-planner/multi-seed/adaptive-margin/smooth-control claim. Reference segment collision-free claims require positive certified Lipschitz lower bounds.

## 45. Server report

/disk1/zlab/maintenance_records/eth3d_single_map_fas_cbf_module_stress_benchmark_v1/report/REPORT_TRAIN_ONE_ETH3D_3DGS_MAP_AND_RUN_FAS_CBF_MODULE_STRESS_BENCHMARK_V1.md

## 46. Downstream handoff

/disk1/zlab/maintenance_records/eth3d_single_map_fas_cbf_module_stress_benchmark_v1/report/downstream_handoff.json

## 47. Only next task

`REFINE_FAS_CBF_STRESS_SCENARIO_ACTIVATION_ON_FROZEN_ETH3D_MAP_V1`
