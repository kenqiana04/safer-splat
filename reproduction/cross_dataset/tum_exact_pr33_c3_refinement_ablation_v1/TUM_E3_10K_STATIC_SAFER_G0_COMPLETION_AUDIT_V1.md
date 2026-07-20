# TUM E3 10K Static SAFER Map and G0 Completion Audit V1

This commit corrects an ordering error in the preceding PR #36 report: the E3 10k raw-depth result was known, but the static SAFER map, frozen-query, gradient, continuity, and immutability evidence had not yet been run. The prior result is preserved as historical evidence; the final status below is recomputed after this completion audit.

## Frozen inputs and recovery

- E3 checkpoint: `/disk1/zlab/maintenance_records/tum_exact_pr33_c3_refinement_ablation_v1/final_candidate/E3_LATE_DEPTH_HOLD_AND_LOCK_10000/NONFORMAL_C3_METRIC_SEED_PLUS_DEPTH/splatfacto/seed20260716_10000/nerfstudio_models/step-000009999.ckpt`, SHA-256 `92e801681afe3f4d62f6679efc3251db6b9c09a6a118f986bf47b730e9bfdc87`.
- The historical E3 output did not retain `config.yml`. A task-owned reconstruction from frozen V1R6 config, the immutable E3 launcher/source and the E3 load target produced config SHA-256 `4d56ff2314fb5e1956ce9d3052c3c06b406e6e6db184723e1a5c1ea0db877b41`. Its task-owned checkpoint path is a symlink to the historical checkpoint; no checkpoint copy or modification was made.
- E3 source gate SHA is `96d1fe63019f04824c9dc4949f91d30627344bb8de05cd62ae3d33c2f3944947`; transforms SHA is `b6a685f4b1a5b2ff3bb9b389c63a138a58119b19dd5cb6d7f671282aeecad29a`; metric-seed SHA is `c5d69bbc965f16147842ad9813eca6d41d9556dd6af602e5b5049402a12e8b56`.
- PR #32 adapter provenance is commit `a45c74fffb706e2f0188c10a35e7654957ce16c8`, raw blob `adabb220a4f34ea199390b43394cc4a7c23f8dff`; the server checkout lacked that historical object, so its exact local Git-object bytes were exported into the task-owned attempt directory.

## Static adapter and map

- Nerfstudio loaded `TumMetricDepthSplatfactoModel` at checkpoint step `9999`. All `330811` Gaussians were retained: no opacity, oversized, or map-scale filter was applied.
- Means are finite; invalid scales, bad quaternions, and invalid covariances are all `0`. Activated opacity range is `0.0008409237489104271` to `1.0`.
- Map bounding box is `[-6.125305652618408, -8.264093399047852, -2.6391043663024902]` to `[7.722389221191406, 3.58097767829895, 5.766269683837891]`, diagonal `20.067750930786133`; camera expanded-bbox inclusion is `1.0`. No coordinate transform, axis conversion, pose scale, or extra global scale was applied.
- Static `splat.gsplat_utils.GSplatLoader` construction passed with count before/after both `330811`.

## Frozen 908-point static query, gradient, and continuity

- The PR #32 query order was reconstructed from its preserved immutable generator semantics and frozen V1R6 map identity: `300` camera centres, `540` signed fixed axis offsets, `64` C-order grid points, and `4` fixed signed out-of-map probes. It has SHA-256 `5d0b971c40adc27915a23c1c5da7cc2b260edb07e0f8d6c223fdd8736519d5d2` as float32 C-order bytes.
- Official `GSplatLoader.query_distance(distance_type=ball-to-ellipsoid, radius=0.0)` ran three times: A/B/C each have `908/908` finite h values and are exactly equal. h statistics are min `-3.367492536199279e-05`, median `0.013770835008472204`, mean `0.2860042392110675`, p95 `0.126198985427618`, max `77.10350799560547`; negative count is `1`.
- h is the repository ellipsoid safety value, not metre clearance and not a collision proof.
- Core `real_get_root` uses in-place bisection updates, which block reverse-mode autograd. The task-owned wrapper uses the identical 25-step bisection and h formula with functional `where` updates only. Its h values have max absolute difference `0.0` and identical active Gaussian indices versus official query values. Two autograd runs have `908/908` finite gradients, zero nonfinite values, exact equality, and gradient-norm p95 `0.7096592724323273`.
- Continuity uses the reconstructed PR #32 contract of `299` ordered adjacent camera-centre pairs, with no smoothing or result-driven epsilon. It is finite, has p95 `|delta h|` `0.025112080574035613`, no outliers above the recorded `0.1` threshold, and status `PASS`. This remains a numerical h diagnostic only.

## Strict G0 result and boundary

All frozen input hashes were unchanged before/after the audit. No optimizer step, new checkpoint, training process, formal training, V1R7, navigation, SAFER rollout, controller, dynamics, CBF-QP, or G1 ran. GPU 1 was released after the audit with no compute process.

Raw E3 depth remains overlap `1.0`, AbsRel `0.23898788744139324`, RMSE `0.5588985630282832`, delta1 `0.5833243883404367`, delta2 `0.8224508122670446`, delta3 `0.9241887650699403`, median ratio `0.9569382071495056`. The static technical gate and full degraded gate pass. The acceptable depth/G0 gate fails solely because `delta1 < 0.75`.

Final status: `PASS_TUM_EXACT_C3_REFINEMENT_DEGRADED_DIAGNOSTIC_ONLY`.

`formal_protocol_candidate=false`; `g1_authorized=false`. The only recommended next task is `TUM Geometry-Prior and Surface-Geometric-Loss Ablation V1`, requiring separate authorization.
