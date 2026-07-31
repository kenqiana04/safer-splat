# ARKitScenes Raw SplaTAM Learned 3DGS Qualification V1

This is the sole fail-closed continuation of PR #66. It uses only Apple official
ARKitScenes raw assets and official SplaTAM source. Candidate order is frozen by
`SHA-256("ARKITSCENES_RAW_CANDIDATE_V1:{visit_id}:{video_id}")`; no more than three
complete candidate videos may be downloaded, no map training begins before raw,
join, coordinate, split, and hard-benchmark prechecks pass, and controller
benchmark count remains zero.

The required raw asset contract is `mesh`, `confidence`, `lowres_depth`,
`lowres_wide.traj`, `lowres_wide`, and `lowres_wide_intrinsics`. FARO is excluded
unless the frozen Apple source provides a complete metric ARKit-world join.

The baseline uses official GT poses and the SplaTAM map-only route. The only
conditional variant changes the training depth mask to `confidence == 2`; it is
forbidden when the baseline passes and cannot change any other frozen parameter.
