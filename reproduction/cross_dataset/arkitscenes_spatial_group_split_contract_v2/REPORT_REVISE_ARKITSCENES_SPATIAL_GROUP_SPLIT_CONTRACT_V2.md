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

## Canonical Git-blob identity correction

The split records, groups, frame order, thresholds, and DP result are unchanged. The two CSV identities were corrected from pre-commit CRLF generation hashes to committed LF Git-blob SHA-256 values under `CANONICAL_GIT_BLOB_BYTES_SHA256_V1`. Legacy values remain in the V2 contract as non-authoritative historical evidence.

- TRAIN legacy `b2d66720fbb0bc7acc998a81e073a9e4774ece7e3ce2900651ff28bf921c2404` → canonical `167066916ce1a3281ac754dfdeec37ada9f5b0e31227c731c94cebb698a2a6e3`
- HELDOUT legacy `670255f2e00f04a0e462e1a83cd4c4d0344e92906604aba9312aa7baabb3b78e` → canonical `7b65f741e901690f2a723579d75200eebe7b9e77b0cd57c030d4a14d0474c0c7`
- Split identity `54f8c9e68ab0e1129be776fc6e911e6ee2011d75123626227ce7cbaa2a660204` → `97a707510227271d12859ee78defc0d6170cc24cb67e423568cd1a72e3345dee`; reason: EOL canonicalization only, semantic change count 0.
