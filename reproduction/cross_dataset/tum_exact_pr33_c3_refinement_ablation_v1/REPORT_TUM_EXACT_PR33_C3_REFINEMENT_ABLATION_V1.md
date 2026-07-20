# TUM Exact PR33 C3 Refinement Ablation V1

Result: `PASS_TUM_EXACT_C3_REFINEMENT_DEGRADED_DIAGNOSTIC_ONLY`.

## Correction and G0 Completion Audit

The previous PR #36 report made this degraded classification before the required static SAFER map/query/gradient/continuity audit had completed. That was an ordering error, not a training, payload, command, config, or Git-object failure. This correction commit preserves every original smoke, 6k, 10k, raw-depth, and source-gate record and recomputes the final status only after the missing static evidence was collected.

E3 is the selected union of late depth hold and refinement lock. It is an independent 10k nonformal diagnostic checkpoint at `/disk1/zlab/maintenance_records/tum_exact_pr33_c3_refinement_ablation_v1/final_candidate/E3_LATE_DEPTH_HOLD_AND_LOCK_10000/NONFORMAL_C3_METRIC_SEED_PLUS_DEPTH/splatfacto/seed20260716_10000/nerfstudio_models/step-000009999.ckpt`, SHA-256 `92e801681afe3f4d62f6679efc3251db6b9c09a6a118f986bf47b730e9bfdc87`. Its historical output did not retain `config.yml`; a task-owned config was reliably reconstructed from the frozen V1R6 config, E3 launcher/source and exact checkpoint target, SHA-256 `4d56ff2314fb5e1956ce9d3052c3c06b406e6e6db184723e1a5c1ea0db877b41`. The checkpoint is referenced by a task-owned symlink only.

The E3 source gate SHA is `96d1fe63019f04824c9dc4949f91d30627344bb8de05cd62ae3d33c2f3944947`; transforms and metric-seed SHA-256 are respectively `b6a685f4b1a5b2ff3bb9b389c63a138a58119b19dd5cb6d7f671282aeecad29a` and `c5d69bbc965f16147842ad9813eca6d41d9556dd6af602e5b5049402a12e8b56`. All were unchanged pre/post audit.

## Original training and raw-depth evidence

All smokes and 6000-step runs exited at their prescribed final steps. Fixed 60-frame metrics were E0 `0.31969/0.48200/0.96117`, E1 `0.25912/0.56317/1.00220`, E2 `0.28393/0.49383/0.93851`, and E3 `0.24520/0.57117/0.96633` for AbsRel/delta1/ratio. E3 won that fixed ranking and was independently trained from scratch to step 9999.

E3 10k raw metrics are overlap `1.0`, AbsRel `0.23898788744139324`, RMSE `0.5588985630282832`, delta1 `0.5833243883404367`, delta2 `0.8224508122670446`, delta3 `0.9241887650699403`, and median ratio `0.9569382071495056`. This single-seed ablation is not a significance claim.

## Completed static SAFER evidence

- PR #32 adapter source: commit `a45c74fffb706e2f0188c10a35e7654957ce16c8`, blob `adabb220a4f34ea199390b43394cc4a7c23f8dff`. The unchanged semantics are exp(raw scales), sigmoid(raw opacities), normalized wxyz, covariance `R @ diag(scale)^2 @ R.T`, no filtering, and `GSplatLoader.query_distance`.
- E3 loaded `TumMetricDepthSplatfactoModel` at step 9999. It contains `330811` Gaussians; means are finite, invalid scales/bad quaternions/invalid covariances are all `0`, and opacity is `[0.0008409237489104271, 1.0]`.
- Map bbox is `[-6.125305652618408, -8.264093399047852, -2.6391043663024902]` to `[7.722389221191406, 3.58097767829895, 5.766269683837891]`, diagonal `20.067750930786133`; expanded camera-bbox inclusion is `1.0`. There is no coordinate mismatch, parser/pose scale conversion, or map rescale.
- Static map build passed with `330811` Gaussians before and after. The frozen 908-query identity is SHA-256 `5d0b971c40adc27915a23c1c5da7cc2b260edb07e0f8d6c223fdd8736519d5d2`: 300 camera points, 540 fixed offsets, 64 grid points, and four out-of-map probes in exact PR #32 order.
- Query A/B/C each returned `908/908` finite values and are exact repeats. h min/median/mean/p95/max are `-3.367492536199279e-05`/`0.013770835008472204`/`0.2860042392110675`/`0.126198985427618`/`77.10350799560547`; one h is negative. h is a repository safety-field value, not metre clearance.
- Autograd uses a task-owned non-inplace algebraic expression only because the core bisection's in-place table invalidates PyTorch's reverse graph. Its h values differ from official query by `0.0` and have identical active indices. Gradient A/B are exactly equal; all `908` are finite, none are nonfinite, and norm p95 is `0.7096592724323273`.
- The 299 ordered adjacent-camera continuity pairs have p95 `|delta h|` `0.025112080574035613`, no discontinuities above `0.1`, and `PASS`. This is numerical continuity evidence only, not a collision or navigation-safety proof.

## Strict classification and boundary

The internal G0 gate is not a public benchmark. Static map, query, gradient, continuity, and immutability all pass, so the full degraded diagnostic gate passes. Acceptable depth and G0 remain false because delta1 `0.5833243883404367 < 0.75`.

`formal_protocol_candidate=false`; `g1_authorized=false`. No formal training, V1R7, navigation, SAFER rollout, controller, dynamics, CBF-QP, or G1 was executed. GPU 1 was released with no residual compute process. The separately authorized next task, if desired, is `TUM Geometry-Prior and Surface-Geometric-Loss Ablation V1`; it must not be started automatically.
