# TUM E3 Bounded Hyperparameter Sweep V1

## Result

`PASS_TUM_E3_BOUNDED_SWEEP_DEGRADED_IMPROVEMENT`

This was a bounded, single-seed coordinate search, not a new method or a full hyperparameter optimization. All eight permitted fresh 6000-step candidates completed, followed by exactly one independent 10000-step run for `C_L050_K2000_B020` (late lambda 0.50, refinement lock 2000, Smooth-L1 beta 0.20). No formal training was started.

## Final candidate and fixed-60 metrics

The final checkpoint is step 9999, has 177011 Gaussians, and SHA-256 `475c222e1010dde0c4f1ac4ba9da077a844518c5476d45ea50cb3f9ea06a4d21`.

| Metric | Final value |
| --- | ---: |
| AbsRel | 0.188127 |
| SqRel | 0.105291 |
| RMSE | 0.477082 |
| RMSElog | 0.265928 |
| delta1 | 0.685632 |
| delta2 | 0.902670 |
| delta3 | 0.972126 |
| median predicted/GT ratio | 0.992987 |

The result is a meaningful improvement within the bounded search, but not G0 acceptable: delta1 remains below the preregistered 0.75 threshold. The selected 6000-step candidate was promoted only once to 10000 steps; there was no retry or reuse as a formal attempt.

## Static SAFER audit on the final checkpoint

The final checkpoint, source, reconstructed config, seed, transforms, and base config passed the immutable-hash gate. The deterministic map had 177011 Gaussians with no filtering or reordering. All 908 static queries were finite and exactly reproducible; the functional gradient path was finite for all 908 queries, contained no zero or non-finite gradient, and was exactly reproducible. The 299-pair continuity diagnostic passed with zero discontinuities. Gaussian numeric checks found zero non-finite Gaussians, invalid covariances, invalid scales, or bad quaternions.

The static technical gate therefore passed. This does **not** make a collision-proof, metre-clearance, navigation, or G1 claim: repository `h` remains an ellipsoid safety value and two static points were negative. The metric gate is explicitly rejected because final delta1 is 0.685632, not at least 0.75.

## Boundaries and next step

No V1R7, formal output, checkpoint candidate, navigation, SAFER rollout, controller, dynamics, CBF-QP, or G1 execution occurred. The next bounded research task should test a geometry prior or surface-geometric loss ablation rather than perform further unbounded tuning.

Evidence files: `input_identity_summary.json`, `sweep_candidate_results.json`, `final_candidate_summary.json`, `static_safer_geometry_gate.json`, and `validation_result.json`.
