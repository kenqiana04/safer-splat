# Replica RGB-D Gaussian Mapping Frontend Qualification V1

**FINAL_STATUS:** `NO_REPLICA_GAUSSIAN_FRONTEND_QUALIFIED`

**FINAL_DECISION:** `DO_NOT_START_REPLICA_FULL_MAP_TRAINING`

## Scope and frozen inputs
Replica RGB-D V3 is rehashed before execution. The frozen design is GT-pose map-only: 30 train-only locations, 60 mapping views, and 30 within-train yaw holdouts.

## Why no full training
Full 270-frame mapping was not authorized by this qualification task.

## Candidates
Only the frozen official SplaTAM and Gaussian-SLAM archives are considered; no third method was added.

## Frontend code and environments
Repository commits and environment identities are recorded in the asset and environment audit.

## GT-pose map-only capability
Tracking and pose updates are disabled in task-owned adapters; no scale/Sim(3)/ICP fitting is performed.

## Camera and coordinate contract
The shared pinhole, metric-depth, and fixed OpenGL-to-OpenCV camera-frame contract is recorded in the input contract.

## Official Replica evaluation
Official Replica eval frames used: 0. The holdouts are within the frozen train split only.

## Pilot locations and yaw split
The registry freezes 30 SHA-selected train locations, mapping yaw 0/-60, and yaw +60 holdouts.

## MST ingestion order
The fixed map-only order is recorded with its SHA-256 in the task root.

## Frozen configurations
Frontend core parameters remain at their official Replica values. Dataset paths, frame lists, intrinsics, GT-pose, tracking-disable, and outputs are task-owned adaptations only.

## Smoke results
SplaTAM: `SMOKE_RENDER_FAILURE`. Gaussian-SLAM: `SMOKE_ALGORITHM_FAILURE`.

## Qualification pilot results
SplaTAM: `NOT_AUTHORIZED_DUE_TO_SMOKE`. Gaussian-SLAM: `NOT_AUTHORIZED_DUE_TO_SMOKE`.

## Smoke canonical export
SplaTAM: `CANONICAL_EXPORT_PASS`. Gaussian-SLAM: `NOT_EXECUTED`.

## Canonical export after qualification pilot
SplaTAM: `NOT_AUTHORIZED_DUE_TO_QUALIFICATION_PILOT`. Gaussian-SLAM: `NOT_AUTHORIZED_DUE_TO_QUALIFICATION_PILOT`.

## Common evaluator
One pre-frozen common Gaussian renderer/evaluator is used for all completed maps; method-native depth metrics are not used to select a frontend.

## Depth geometry metrics
SplaTAM completed-smoke metrics: `{'absrel': 0.21556426817551255, 'delta1': 0.6691799516839645, 'delta2': 0.7933246104831444, 'delta3': 0.8946188347362878, 'median_depth_ratio': 0.9672450348734856, 'nonfinite_prediction_count': 0, 'psnr': 15.725835798288253, 'rmse': 0.6422863872721791, 'rmse_log': 0.5790505595505238, 'sqrel': 0.22711597080342472, 'ssim': 0.3575121503230737, 'valid_predicted_depth_fraction': 0.9892537434895833, 'valid_rgb_coverage': 1.0}`; pilot metrics: `{}`. Gaussian-SLAM completed-smoke metrics: `{}`; pilot metrics: `{}`.

## Geometry alignment boundary
No ground-truth fit, scale fitting, Sim(3), ICP, or map alignment is applied.

## Metric map and export identity
SplaTAM's completed smoke map is canonicalized without filtering. No post-pilot map exists because both pilots were correctly gated off.

## Map structure
SplaTAM: `NOT_AUTHORIZED_DUE_TO_CANONICAL_EXPORT`. Gaussian-SLAM: `NOT_AUTHORIZED_DUE_TO_CANONICAL_EXPORT`.

## SAFER G0
SplaTAM: `NOT_AUTHORIZED_DUE_TO_COMMON_EVALUATION`. Gaussian-SLAM: `NOT_AUTHORIZED_DUE_TO_COMMON_EVALUATION`.

## SplaTAM qualification
SplaTAM qualified: `False`.

## Gaussian-SLAM qualification
Gaussian-SLAM qualified: `False`; config resolution `FRONTEND_CONFIG_NOT_QUALIFIED`.

## Infrastructure versus science
The Gaussian-SLAM failure is a deterministic incompatibility between the frozen official 600,000-point new-submap parameter and a 640x480 input, not a permission to tune or retry. SplaTAM completed its smoke map but failed the pre-frozen shared geometry gate. The initial SplaTAM launcher allowed native mapping-frame diagnostic files to be written; they were neither official eval nor used for comparison, and no smoke rerun was performed.

## Attempt preservation
Both terminal smoke records and logs are retained. No completed map, terminal result, or failure log was deleted, replaced, or rerun.

## Artifact validation
The compact JSON, report, and figure contract is validated locally; raw checkpoints, caches, render arrays, and logs are excluded from Git.

## No automatic winner claim
A small pilot cannot establish a general winner; no frontend is selected from unavailable or failed gates.

## No formal evaluation or control
No full map, official eval, navigation, CBF-QP, Start-Safe, Risk-Aware, Recovery/V4-C, TUM, or formal output is run.

## Final status
NO_REPLICA_GAUSSIAN_FRONTEND_QUALIFIED

## Final decision
DO_NOT_START_REPLICA_FULL_MAP_TRAINING

## Next task
DIAGNOSE_REPLICA_GAUSSIAN_MAPPING_GEOMETRY_FAILURE_V1
