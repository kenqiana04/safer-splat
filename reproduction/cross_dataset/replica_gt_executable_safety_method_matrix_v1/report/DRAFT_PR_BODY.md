## Summary

Freezes the complete Replica GT B0-B3 executable-safety method matrix required by the PR #85 fairness blocker.

- PR #85 is preserved and its blocker is reproduced from canonical PR #84 blobs.
- PR #84 certifier semantics remain unchanged.
- B2/B3 share primary control, gates, and deterministic braking; B3 only adds `REPLICA_GT_REPRESENTED_MAP_DIRECTIONAL_ALTERNATIVE_LIBRARY_V1` with six fixed slots.
- Global library SHA-256: `3d491876234161d4e881ec1227c505cb07c0af00d5e881c5289fdf1f1577c6fe`.
- Frozen geometry: `n=(p-c_j)/||p-c_j||_2`, `t_g=normalize(g-(g^Tn)n)`, `t_a=n×t_g`; the axis fallback selects the least-aligned x/y/z axis deterministically.
- Frozen controls: `u_box(d)=0.1d/||d||_∞`; brake-biased directions are projected into `v^Td<=0` before box scaling.
- Fixed-slot availability and canonical float64 de-duplication retain the earlier slot; no unavailable or duplicate control is passed to B3.
- The generator has no reference input and no benchmark search/outcome path.
- Synthetic properties, three-process determinism and a 25-record generator-only Replica smoke pass.

## Claim boundary

This is method-design-only. It does not claim alternative effectiveness, rescue, collision reduction, safety/progress/runtime superiority, complete search, or deployment readiness.

`FINAL_STATUS=PASS_REPLICA_GT_EXECUTABLE_SAFETY_METHOD_MATRIX_FREEZE_V1`

`FINAL_DECISION=RESUME_REPLICA_GT_EXECUTABLE_SAFETY_ACTIVATED_BENCHMARK`

Only next task: `RESUME_REPLICA_GT_EXECUTABLE_SAFETY_ACTIVATED_BENCHMARK_V1`.
