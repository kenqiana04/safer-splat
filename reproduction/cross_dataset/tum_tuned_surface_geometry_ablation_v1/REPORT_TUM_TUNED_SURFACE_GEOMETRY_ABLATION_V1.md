# TUM Tuned-Baseline Geometry-Prior and Surface-Geometric-Loss Ablation V1

## Result

`PASS_TUM_TUNED_SURFACE_GEOMETRY_DEGRADED_IMPROVEMENT`. The static SAFER technical audit passed, but this is an internal G0 diagnostic, not a public benchmark or a formal-training authorization. The selected nonformal candidate S2 reached delta1=0.671166, below the strict 0.75 acceptable threshold; it is therefore degraded improvement only.

## Frozen baseline and inputs

The PR #37 tuned baseline is C_L050_K2000_B020: late depth lambda 0.50, lock step 2000, depth beta 0.20 m, depth lambda 0.10, seed 20260716, and fixed 240/60 split. Input identities, source restoration, transforms, and metric seed all matched in `input_identity_summary.json`. No further parameter search was performed.

The prior is deterministic RGB-D geometry, not learned: cKDTree k=17 (16 nonself), workers=1, eps=0, p=2, PCA tangent frame, wxyz quaternion and anisotropic scales. It contains 359,140 valid points, zero fallbacks, and SHA-256 `b4be9de894858f7f07d24a9156721cb74a6a3dbd4bd97975c905650bbef88dbc`. Surface targets are train-only; evaluation uses a separately generated 60-frame target set.

## 6K screen and selection

S2 was the sole qualified candidate under `MEANINGFUL_SURFACE_IMPROVEMENT_SCREEN_PASS`: delta1 gain 0.025943, AbsRel delta -0.016844, and point-to-plane MAE improvement 5.21%. S1 improved normal median error but did not meet the frozen delta1/plane gate; S3 also did not qualify. This is a single-seed engineering ablation, not statistical significance.

## Independent 10K result

S2 was trained from empty task-owned output, no resume/load, to step 9999. Fixed-60 metrics: AbsRel 0.197457, RMSE 0.499080, delta1 0.671166, delta2 0.888305, delta3 0.957330, ratio 0.996289. Surface MAE/RMSE: 0.211241/0.352936; normal mean/median: 56.168/58.832 degrees. Gaussian count 188701; nonfinite and invalid covariance counts are zero.

## Static SAFER boundary

The static map build passed; 908/908 queries and gradients were finite and exactly deterministic, and all 299 continuity pairs passed. The run did not instantiate a controller, dynamics model, QP, trajectory runner, navigation, or SAFER rollout. No formal training, V1R7, G1, checkpoint candidate, or automatic next run was created.

## Next step

Do not promote this result to formal training automatically. The recommended separately authorized follow-up is `TUM Dedicated RGB-D Gaussian Baseline Comparison V1`.
