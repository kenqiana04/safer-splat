# Replica Render Protocol V3 Pre-Render Coverage Qualification

**FINAL_STATUS:** `PASS_REPLICA_RENDER_PROTOCOL_V3_PRE_RENDER_COVERAGE_QUALIFICATION`

## 1. Frozen V1/V2/asset-audit boundary
The frozen asset audit remains authoritative: V1 has 32 joint RGB/depth failures caused by direct `mesh.ply` geometry-coverage gaps; frame_0034 is a separate sparse, dark RGB-only view. V3 is `NEW_PREQUALIFIED_REPLICA_RENDER_PROTOCOL_V3`, never a repaired, cleaned, filtered, or republished V1 dataset. It does not delete V1 failures.

## 2. Asset and protocol contract
The direct formal asset remains `mesh.ply` (SHA-256 `274677d9b7caa413230363b68f4aa472e5cc1afe87e422a489fa1b7d844c6182`) and the original navmesh remains SHA-256 `32296d6457d3855ffe172cf1970364559def5dd15892e149b44d0bc7c6b7e938`. The semantic mesh was not substituted: it is a distinct semantic asset and would change the formal RGB-D asset identity.
The V3 contract was written before any candidate call (SHA-256 `ddd147f908537165c40a34b412cd21c3cbfb5a0615871375d02adecbbfaec6f7`). It freezes seed 20260728, 2,048 raw navmesh calls, at most 1,024 candidates, 1.50 m camera height, yaw offsets [0,-60,+60], 41x31=1271 independent rays/view, 0.10 direct/depth thresholds, 0.05 RGB threshold, 100 final locations, and a 90/10 location-level split.

## 3. Candidate and pose generation
Raw candidate calls: 2048; finite/navigable/snap-valid/in-bounds: 2048; hash-sorted, 0.05 m greedily deduplicated unique locations: 1024. A second fresh generation matched exactly (position-array SHA `f35e6a27559368fa42b2569fe9bae8bdadca8013d7dad19d8344a3a2b8ebd7dc`).
Base yaw is derived solely from `SHA256(REPLICA_V3_BASE_YAW:location_hash)`, taking its first eight big-endian bytes and mapping to [0,360); no candidate coverage or RGB content can change an orientation. Each candidate has the V1-verified Y-up, no-pitch/no-roll three-yaw c2w triplet.

## 4. Independent direct-mesh qualification
The CPU-only float64 direct-mesh BVH evaluated 3072 candidate views and 3904512 rays. View qualification requires finite valid near/far hit fraction >=0.10 and a front-facing hit; 1858 views and 373 full location triplets passed. Reference A/B agreed on 8/8 required key rays.

## 5. Fresh Habitat pre-render qualification
Habitat ran diagnostic-only fresh OS subprocesses and fresh Simulators per location. Stage 1 evaluated 160 locations and passed 156; Stage 2 and Stage 3 were not required. Total: 160 locations / 480 views / 156 triplet-pass locations.
Cross-validation found 4/480 independent-pass/Habitat-fail views (0.008333), below the 5% contradiction gate; Pearson coverage correlation was 0.9989964808358326.

## 6. Spatial selection, split, and frozen manifest
Hash-tied greedy farthest-point selection froze 100 Habitat-qualified locations. Minimum pairwise separation is 0.359149 m; the selection occupies 83 XZ cells at 0.50 m. Frozen V1 exact/near (<0.10 m) location overlap is 0/2 and was reported only, never used for selection.
The deterministic location-level split is 90/10 locations and 270/30 frames, with location leakage 0. The new manifest contains 300 rows; CSV SHA `6db89bc0dafaa5993b452216be1205ec9db0a1d9da23b9bc2b9029fabc2113d6`, JSON SHA `f029de724f33a2788c1f6570b5d730ec06f3223a2d512c38a0427ca9c1d14b2b`, transforms SHA `ec50b63a1263d9f6e355a6d5010ab79738d92d59f8bec481150d86f3145d888f`, pose-array SHA `0bc952fec3236d117b33d0d62085a60412b96e2174ab0a31c7c5fec204789622`.

## 7. Frozen-manifest repeatability
The 30 hash-selected frozen frames covered yaw offsets [-60, 0, 60] and splits ['eval', 'train']. Fresh-process A/B results were A 30/30, B 30/30, disagreements 0.

## 8. Decision, boundaries, and only next task
The generated figures distinguish raw candidates, independent passes, Habitat passes, final selection, and frozen V1 locations. No formal 300-frame RGB-D render, dataset publication, Gaussian training, SAFER/CBF, Start-Safe, Risk-Aware, Recovery/V4-C, or TUM rollout ran. Camera-protocol qualification is not RGB-D publication, Gaussian mapping qualification, SAFER baseline qualification, or FAS-CBF evaluation.

**Decision:** `FREEZE_REPLICA_APARTMENT_0_RENDER_PROTOCOL_V3`

**Only next task:** `RENDER_VALIDATE_AND_ATOMICALLY_PUBLISH_REPLICA_RGBD_V3`
