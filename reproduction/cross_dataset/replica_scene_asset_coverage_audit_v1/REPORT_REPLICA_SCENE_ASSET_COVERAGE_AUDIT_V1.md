# Replica Scene Asset Geometry, Culling, Material and Render-Coverage Audit V1

## Result

`PASS_REPLICA_ASSET_AUDIT_REQUIRES_NEW_CAMERA_PROTOCOL`

The upstream V2 diagnosis is preserved: 33 RGB exceptions, 32 depth exceptions, 32 joint exceptions, and one separate RGB-only frame (`frame_0034`). Texture cannot explain the 32 joint failures because their Habitat depth is zero and the independent CPU float64 triangle raycaster has zero valid hit fraction for every one of the 32, while normal frozen controls have a median hit fraction of 0.476078.

The direct V1 Habitat stage is `mesh.ply`, with unit scale, material shader, force-flat-shading and frustum culling. The source PLY has vertex RGB, stored vertex normals, no UVs and no material/texture assignment; its external Ptex payloads are not referenced by the direct stage. Habitat's Python binding exposes one active stage asset but not individual drawable enumeration.

## Independent geometry evidence

Reference A was the task-owned accelerated CPU BVH float64 Moller-Trumbore implementation. Reference B was a separate brute-force float64 Moller-Trumbore execution on four frozen key center rays; agreement was 4/4. The 32 joint frames have zero independent any-hit, front-facing-hit and back-facing-only fractions. Therefore they meet the preregistered true coverage-gap indication, not a texture, culling, import or clipping claim.

`frame_0034` has sparse valid depth and a 0.007059 independent hit fraction. It is classified separately as `RGB_ONLY_LEGITIMATELY_DARK_VIEW_UNDER_V1_THRESHOLD`. It does not explain the joint failures.

## Diagnostic variants and boundaries

The fixed 166 terminal fresh-subprocess diagnostic results used only task-owned variants marked `DIAGNOSTIC_ONLY_NOT_A_FORMAL_REPLICA_ASSET`: flat-untextured same geometry, reversed-face double sided diagnostic, connected-component flat IDs, and the existing official semantic mesh comparison. A/B/C retain zero depth on all joint failures. The semantic-mesh comparison does produce depth, but it is a distinct semantic asset, not a qualified RGB render replacement; it demonstrates that a geometry substitute would change the V1 asset contract rather than repair the frozen direct-Ply source. The initial first-frame capture had a task-owned NPY writer failure after observation but before any terminal JSON/depth record; it is preserved in the server log and the terminal schedule contains exactly 166 results. None was made a formal asset and none changes V1 staging, manifest, poses, scale, resolution, HFOV, near/far, height or split.

The conclusion is `PURE_GEOMETRY_COVERAGE_DEFECT`. Repair feasibility is `NOT_FIXABLE_WITHOUT_CHANGING_SCENE_GEOMETRY_OR_CAMERA_PROTOCOL`. The only next task is `DESIGN_REPLICA_RENDER_PROTOCOL_V3_WITH_PRE_RENDER_ASSET_COVERAGE_QUALIFICATION`.

No 300-frame rerender, dataset publication, Gaussian training, SAFER/CBF, Start-Safe/Risk-Aware/Recovery, or TUM execution occurred. Replica scene-asset qualification is not RGB-D dataset qualification, Gaussian mapping qualification, SAFER baseline qualification, or FAS-CBF evaluation. TUM remains `CLOSE_TUM_NAVIGATION_BENCHMARK_KEEP_SAFETY_CASE_STUDY`.
