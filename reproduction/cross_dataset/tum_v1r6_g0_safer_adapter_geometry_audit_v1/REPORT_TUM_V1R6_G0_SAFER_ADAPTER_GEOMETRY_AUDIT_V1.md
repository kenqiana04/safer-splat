# TUM V1R6 G0 SAFER Checkpoint Adapter and Geometry Audit V1

## Joint result

`BLOCKED_BY_TUM_V1R6_GEOMETRY_INVALID_FOR_SAFER`. Technical adapter status is `PASS_TUM_V1R6_G0_SAFER_ADAPTER_TECHNICAL_AUDIT`, but raw fixed-split metric depth geometry is `GEOMETRY_INVALID_STOP`. G1 is not authorized.

## Immutable inputs and loader contract

- Checkpoint `/disk1/zlab/formal_splatfacto_runs/tum_fr1_room_splatfacto_v1r6/splatfacto/20260717_070309/nerfstudio_models/step-000029999.ckpt`, SHA-256 `4941bf1faba1aed31949ee4114898c0eec33ff1a46b7bcadad6d06f5f647ae6b`, size `491777938`; config SHA `c9a103c38483f76aed4701489084347566c2437719ae54ea962017469c708cfe`; transforms SHA `b6a685f4b1a5b2ff3bb9b389c63a138a58119b19dd5cb6d7f671282aeecad29a`.
- Nerfstudio loaded `VanillaPipeline` / `SplatfactoModel` at step 29999, in eval mode. The adapter uses `eval_setup`, extracts all `680617` Gaussians without filtering, applies `exp(raw_scales)` and `sigmoid(raw_opacities)`, and emits wxyz normalized quaternions and `R @ diag(scale)^2 @ R.T` covariance.
- SAFER contract sources: `splat/gsplat_utils.py` (`GSplatLoader.load_gsplat_from_nerfstudio`, `query_distance`); `ellipsoids/covariance_utils.py` (`quaternion_to_rotation_matrix`, `compute_cov`); `dynamics/systems.py` (`DoubleIntegrator`). No core source was changed.

## Gaussian and coordinate evidence

- Means are finite; activated scales strictly positive; quaternions normalized; covariance invalid count `0`; opacity range `0.0009101150208152831` to `1.0`.
- Map bbox `[-6.322019100189209, -6.241601943969727, -5.377645492553711]` to `[6.019745826721191, 6.639648914337158, 6.109530925750732]`; scene diagonal `21.217939376831055`. Camera bbox `[-1.1555999517440796, -1.3490999937057495, 1.1904000043869019]` to `[1.3858000040054321, 0.8600000143051147, 1.6934000253677368]`; expanded bbox inclusion `1.0`.
- Transforms-to-datamanager maximum absolute errors were `5.950927728370914e-08` (train) and `5.7983398527028385e-08` (eval): no axis conversion or pose-scale conversion was applied.
- Internal floater thresholds are descriptive only: oversized fraction `0.00011313264985801652` and low-opacity oversized fraction `0.0`; no Gaussian was filtered.

## Raw depth and metric scale gate

- Fixed all-60-frame raw depth overlap `1.0`; AbsRel `0.791195087240712`, RMSE `1.4457623975669482`, delta1 `0.061905662166267535`, delta2 `0.12020020460069694`, delta3 `0.1802820135601347`, median predicted/GT ratio `0.17006996273994446`.
- Diagnostic global median scaling multiplier `5.879933081005664` is explicitly diagnostic only and does not replace the raw gate. It does not restore a good ratio-distribution result.
- Thus RGB PSNR was not used as a blocker; raw metric depth exposes a geometry/scale mismatch and triggers `raw median predicted/GT depth ratio < 0.50, raw AbsRel > 0.50, raw delta_1_25 < 0.50`.

## Static SAFER geometry only

- Adapter schema comparison has no unresolved fields. Actual static `GSplatLoader` map build passed with `680617` Gaussians and no filtering.
- Actual official `query_distance` ran on `908` fixed points: finite `True`, deterministic exact repeat `True`, finite gradients `True`. h is repository safety h, not metres.
- Continuity was recorded without smoothing (p95 |delta h| `0.018757276798714882`, p95 gradient norm `0.4571736633777615`). Auxiliary signed ellipsoid surface-distance median `0.03947101114564829` is not a replacement for h or metric clearance.

## Navigation boundary and next step

SAFER dynamics are 3D position+velocity, but a TUM handheld camera center is not established as a robot center; no navigation plane, external transform, or start/goal protocol was frozen. Status: `G1_START_GOAL_PROTOCOL_UNRESOLVED`.

No training, resume, retry, navigation, rollout, CBF/QP, SAFER baseline, Risk-Aware, Start-Safe, Discrete-Time Verification, Predictive Recovery, or G1 was executed. Recommended next task: `Repair TUM Map Geometry Before SAFER Evaluation`.
