# ARKitScenes Spatial Group Split Contract V2

`PR67_FORMAL_STATUS=BLOCKED_BY_ARKITSCENES_DATA_OR_COORDINATE_CONTRACT`
`SCIENTIFIC_INTERPRETATION=BLOCKED_BY_FIXED_240_60_SPATIAL_GROUP_SPLIT_CONTRACT`

PR #67 remains unchanged. Both fixed candidates previously passed raw asset validation, strict RGB/depth/confidence/intrinsics/pose joining, metric coordinate audit, and the 20/20/20/10 future hard-benchmark precheck. PRIMARY `42899163` remains V2-ineligible because its immutable V1 keyframe count is 173, below 240. BACKUP `48018874` has 267 V1 keyframes. The old 220/50 lower bound needs 270 total frames, and V1's exact-240-then-exact-60 allocation can leave at most 27 after a 240-frame TRAIN subset.

V1 identities were frozen before reconstruction. V1 keyframes and connected components were reconstructed from the immutable joined manifests, with the original timestamp/center/orientation edge contract and original group hash identity. V2 uses complete V1 groups only, target `floor(0.20*N+0.5)=53`, hard gates TRAIN>=200 and HELDOUT 40–60, and deterministic subset-sum DP with the prescribed lexicographic tie-break.

Selected result: HELDOUT=53, TRAIN=214, HELDOUT groups=5, TRAIN groups=8. The independent validator found zero frame-index, filename, RGB, depth, confidence, pose-timestamp, and group-hash overlap; zero cross-split group edges; zero discarded/duplicate records; and global score agreement. Three fresh processes reproduced all group trees, selected hashes, manifests, split identity, and validation result.

All prohibited counters are zero: no new download, third candidate, environment creation, smoke, training, checkpoint, map, Gaussian export, NVS, geometry/clearance evaluation, SAFER G0, or controller benchmark. GPU 1 was read only: `1, 6 MiB, 0 %`.

## Final

`FINAL_STATUS=PASS_ARKITSCENES_SPATIAL_GROUP_SPLIT_V2`
`FINAL_DECISION=FREEZE_ARKITSCENES_VIDEO_48018874_FOR_SPLATAM_MAPPING`
`ONLY_NEXT_TASK=RESUME_ARKITSCENES_SPLATAM_SMOKE_AND_LEARNED_MAP_QUALIFICATION_V1`

Split protocol only: no mapping training and no geometry result. This revision does not guarantee later training success.
