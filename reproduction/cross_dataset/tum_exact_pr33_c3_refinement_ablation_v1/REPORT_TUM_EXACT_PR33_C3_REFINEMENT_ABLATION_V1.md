# TUM Exact PR33 C3 Refinement Ablation V1

Result: `PASS_TUM_EXACT_C3_REFINEMENT_DEGRADED_DIAGNOSTIC_ONLY`.

All six frozen inputs matched. E0 exactly restores PR33; source gate passed. E1 changes only the effective depth weight from 0.10 before zero-indexed step 3000 to 0.30 from step 3000. E2 changes only the original post-backward route so topology mutation and opacity reset stop at step 3000; E3 is their union. No PR34 R0 class, instrumentation, CPU scalar logging, quantile scan, geometry prior, or surface loss was used.

All smokes and 6000-step runs exited at their prescribed final steps. Fixed 60-frame metrics were E0 `0.31969/0.48200/0.96117`, E1 `0.25912/0.56317/1.00220`, E2 `0.28393/0.49383/0.93851`, and E3 `0.24520/0.57117/0.96633` for AbsRel/delta1/ratio. E3 won the fixed ranking and was independently trained from scratch to step 9999.

E3 10k yielded overlap 1.0, AbsRel 0.23899, RMSE 0.55890, delta1 0.58332, delta2 0.82245, delta3 0.92419, and ratio 0.95694. This is a single-seed engineering ablation, not statistical significance. It meets the degraded diagnostic depth gate but cannot meet the acceptable G0 gate because delta1 is below 0.75; no formal protocol candidate or G1 authorization is produced.

No formal training, V1R7, navigation, SAFER rollout, CBF-QP, or G1 was executed. Recommended next task: TUM Geometry-Prior and Surface-Geometric-Loss Ablation V1, requiring separate authorization.
