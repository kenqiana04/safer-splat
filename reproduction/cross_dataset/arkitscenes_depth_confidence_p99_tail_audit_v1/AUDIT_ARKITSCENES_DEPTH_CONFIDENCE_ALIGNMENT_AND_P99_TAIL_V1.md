# AUDIT_ARKITSCENES_DEPTH_CONFIDENCE_ALIGNMENT_AND_P99_TAIL_V1

This protocol is a pre-training, data-quality and attribution audit for ARKitScenes scene `48018874`, visit `483945`.

## Frozen lineage and inputs

- Base PR: `#71`
- Base head: `1c55f67e7b93b098c672eb09ff483fd8d037fde9`
- TRAIN: 214 canonical frames; raw Git-blob SHA-256 `167066916ce1a3281ac754dfdeec37ada9f5b0e31227c731c94cebb698a2a6e3`
- HELDOUT: 53 structure-only frames; raw Git-blob SHA-256 `7b65f741e901690f2a723579d75200eebe7b9e77b0cd57c030d4a14d0474c0c7`
- Split identity: `97a707510227271d12859ee78defc0d6170cc24cb67e423568cd1a72e3345dee`
- Selected group tuple: `8ad320980bb36edb2accb38629ec3046095c9ef7735fbb748f4e112ee75bd388`
- ARKitScenes authority: `7283761bf26c27570ec59a5dc0f8686fbff07726`
- SplaTAM authority: `da6bbcd24c248dc884ac7f49d62e91b841b26ccc`
- Rasterizer authority: `cb65e4b86bc3bd8ed42174b72a62e8d3a3a71110`

## Fixed masks

- M0_RAW_POSITIVE: `depth_raw > 0`
- M1_CONFIDENCE_GE1: `depth_raw > 0 AND confidence >= 1`
- M2_CONFIDENCE_EQ2: `depth_raw > 0 AND confidence == 2`

No other threshold, crop, morphology, frame-specific rule, frame removal, pose/intrinsic adjustment, ICP, or Sim(3) is permitted.

## Frozen gates

Geometry: median <= 0.05 m, p95 <= 0.15 m, p99 <= 0.30 m, at least 80% frame medians <= 0.10 m, and zero nonfinite results.

Supervision for M1/M2: global retention >= 0.30; at least 90% of TRAIN frames have at least `max(1024, 0.05*M0)` valid pixels; each of eight TRAIN groups has at least 10 supported frames and retention >= 0.20; longest unsupported run <= 5; any zero-valid frame requires independently proven official SplaTAM compatibility.

## Execution boundary

The audit may read raw RGB, depth, confidence, intrinsics, poses, official mesh, and frozen SplaTAM source. It must not instantiate a SplaTAM mapper, create an optimizer, run backward, update parameters, start smoke or training, create a checkpoint or map, render NVS, run clearance/G0/variant/controller work, delete frames, modify raw assets, or modify the PR #71 adapter/mask contract.
