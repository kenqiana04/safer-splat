# Gaussian-SLAM Resolution Adaptation Contract Audit V1

## 1. Why Splatfacto does not continue
Its frozen navigation-map route is closed; this audit performed zero Splatfacto executions.

## 2. Why the SplaTAM gate is not relaxed
The frozen 60/30 pilot remains below delta1=0.75 and received no retraining or threshold change.

## 3. Why Gaussian-SLAM was audited
PR #56 failed before any evaluable map, so source semantics can be resolved without scientific mapping.

## 4. Why 600000 > 307200 is not alone a repair rule
Arithmetic identifies a domain failure, not whether a clamp, scale, or input restoration is official.

## 5. Replica input identity
The published complete tree is `24e21d3bccceb0516ed8b9b49b426964f3954ccd0cd804eedd5846baabd66dcb`; all frozen metadata, selection, order, 300-frame pairing, and split checks passed.

## 6. PR #56 failure evidence
The terminal was `SMOKE_ALGORITHM_FAILURE` on mapping frame 0: `ValueError: Cannot take a larger sample than population when 'replace=False'`.

## 7. Archive and environment
The immutable archive record is `eaec10d73ce7511563882b8856896e06d1f804e3` at `/disk1/zlab/external_baselines/tum_rgbd_gaussian_v1/repos/Gaussian-SLAM_official_archive`. The read-only prefix is `/disk1/zlab/external_baselines/tum_rgbd_gaussian_v1/envs/tum_gaussian_slam_baseline_v1_conda` with Python 3.10.20, PyTorch 2.1.2, and CUDA 12.1.

## 8. Stack-trace classification
The first official failing source line is `src/entities/mapper.py:97` in `Mapper.seed_new_gaussians`.

## 9. Parameter definition and call graph
The value is loaded into the mapper and passed as the exact second positional count to `numpy.random.choice`.

## 10. Sampling replacement semantics
The uniform choice explicitly uses `replace=False`; this audit did not change it.

## 11. Candidate pool definition
`create_point_cloud` returns one row per native image pixel; uniform sampling occurs before zero-depth filtering.

## 12. Config source
The official `room0.yaml` (`71f37b1aee0cd827160056c5a64874a233586ba93b1f50f7d3505ef53f344bdd`) inherits `replica.yaml` (`92fb1477ae7656d589e44597fc3570fa9af98296bf067d900f8df4b9c477c194`), which supplies the 600000 mapping value; the task generated a 640x480 config with the unchanged count.

## 13. Official reference resolution
The official Replica config is 1200x680 (816000 pixels); Replica V3 preprocessing is native 640x480.

## 14. 16-frame census
Each smoke frame has 307200 uniform candidates (minimum/median/maximum all 307200); all 16 are infeasible for 600000 without replacement. Valid-depth counts range from 78753 to 307200, but filtering happens after the failed uniform choice.

## 15. 60-frame census
Each frozen pilot frame likewise has 307200 uniform candidates (minimum/median/maximum all 307200); all 60 are infeasible. Valid-depth counts range from 32099 to 307200 and cannot repair the pre-filter selection error.

## 16. Adapter-bug evidence
No bad candidate aggregation, resize, or mask-before-choice divergence was found; only the incompatible generated configuration context is present.

## 17. Config-mismatch evidence
The official exact count was copied from a different input resolution, supporting `OFFICIAL_CONFIG_SOURCE_MISMATCH`.

## 18. Resolution-cap evidence
There is no cap fallback: source requests an exact count and errors when insufficient.

## 19. Core-hyperparameter evidence
The count is a submap seeding budget and varies across official datasets, so changing it alters initialization density.

## 20. Hypothesis matrix
Config mismatch and core-hyperparameter explanations are supported; cap and semantic-unknown explanations are contradicted.

## 21. Legality standard
All fourteen conditions are required; official derivation and non-core preservation fail here.

## 22. Unique rule
No unique legal adaptation rule exists. Clamp, manual count, and density scale were rejected.

## 23. No-training validation
It is not authorized under RULE_D; no invented effective count was tested.

## 24. Adapted config identity
Both adapted-config artifacts explicitly state `NOT_CREATED_DUE_TO_NO_LEGAL_ADAPTATION`.

## 25. No mapping declaration
Gaussian-SLAM optimizer invocations and mapping iterations are zero.

## 26. No map/checkpoint declaration
No map or checkpoint was created.

## 27. No official evaluation
Official evaluation usage is zero.

## 28. No SAFER/navigation
SAFER navigation and CBF-QP were not run.

## 29. TUM boundary
TUM remains frozen; paired20 identity is retained without execution.

## 30. FINAL_STATUS
`NO_LEGAL_GAUSSIAN_SLAM_RESOLUTION_ADAPTATION_CONTRACT`

## 31. FINAL_DECISION
`CLOSE_GAUSSIAN_SLAM_REPLICA_ROUTE_UNDER_OFFICIAL_CONFIG`

## 32. Only next task
`REPLICA_GAUSSIAN_MAPPING_FRONTEND_STRATEGY_DECISION_V1`
