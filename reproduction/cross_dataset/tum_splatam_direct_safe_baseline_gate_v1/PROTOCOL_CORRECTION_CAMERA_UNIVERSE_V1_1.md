# TUM SplaTAM Direct-Safe Baseline Gate: Camera-Universe Protocol Correction V1.1

## Status

`SUPERSEDED_BY_CAMERA_UNIVERSE_PROTOCOL_CORRECTION_V1_1`

The prior stop record remains historically correct.  Its earlier requirement
for 908 camera centers was an erroneous protocol specification, not an asset
or map identity failure:

`PROTOCOL_SPECIFICATION_ERROR: 908_POINT_STATIC_QUERY_SET_WAS_CONFLATED_WITH_CAMERA_CENTER_COUNT`

## Corrected frozen universe

The sole endpoint universe for V1.1 is
`CANONICAL_TUM_MAP_ALIGNED_CAMERA_CENTER_UNIVERSE_V1`: the 300 frames, in
their original order, in
`/disk1/zlab/cross_dataset_assets/processed/tum_rgbd/freiburg1_room/transforms.json`.

- transforms SHA-256: `b6a685f4b1a5b2ff3bb9b389c63a138a58119b19dd5cb6d7f671282aeecad29a`
- frame / camera-center count: `300`
- float64 `transform_matrix[:3, 3]` array SHA-256:
  `bcee7929b9a7c595c669212972c60f5290e1eceb6834cec66f24a9193ae24d6c`

The 908 points cited previously were the PR #44 synthetic static query set:
300 map-aligned camera centers, 540 perturbations, 64 regular-grid points,
and 4 exterior/extreme points.  They are not 908 transforms or endpoint
camera centers.  There is therefore no canonical-map or transforms-identity
conflict.

## Isolation of invalid V1 calculations

The old server root
`/disk1/zlab/maintenance_records/tum_splatam_direct_safe_baseline_gate_v1`
is preserved, including its historical record, but its pre-correction endpoint
inventory, candidates, bins, and registry are
`INVALIDATED_BY_PROTOCOL_SPECIFICATION_ERROR`.  None may be copied, used for
selection, used for search-budget decisions, or included in V1.1 statistics.

V1.1 starts only in the clean root
`/disk1/zlab/maintenance_records/tum_splatam_direct_safe_baseline_gate_v1_1`.
It re-queries all 300 canonical centers with ball-to-ellipsoid radius `0.015`.
No other TUM frames, interpolation, PR #44 perturbations, grid points, or
extreme points are permitted.

The original blocker was an honest stop after executing the then-frozen but
incorrect cardinality requirement.  It must not be rewritten as though the
task had never been blocked.
