# ARKitScenes depth-confidence alignment and p99-tail audit V1

## Answer first

`FINAL_STATUS=NO_ARKITSCENES_METRIC_DEPTH_INPUT_CONTRACT_QUALIFIED`
`FINAL_DECISION=CLOSE_ARKITSCENES_SPLATAM_MAPPING_ROUTE_WITHOUT_TRAINING`
`Only next task=ETH3D_DELIVERY_AREA_LEARNED_3DGS_QUALIFICATION_V1`

No M0/M1/M2 metric-depth input contract qualifies under the frozen combined geometry and supervision gates. M0 retains adequate supervision but fails p99 (`0.482769 m > 0.30 m`). M1 and M2 pass the unchanged geometry gates, but both fail the preregistered group-support contract because frozen TRAIN groups 3, 6, and 11 contain only 1, 2, and 9 frames respectively, making the required minimum of 10 supported frames arithmetically impossible. M1/M2 also contain 2/4 zero-valid frames, and official SplaTAM's non-tracking depth loss uses an empty masked `mean()`, which the bounded synthetic test confirms is nonfinite.

## PR #71 handoff and why its stop was correct

- Base PR/head: `#71` / `1c55f67e7b93b098c672eb09ff483fd8d037fde9`.
- PR #71 stopped before smoke/training because its 64-frame M0 sample failed p99 while median and p95 passed.
- This audit confirms the same pattern on all 214 TRAIN frames. Stopping before mapper execution was correct: the heavy tail is real under M0 and a replacement validity contract cannot be adopted without violating the frozen supervision gates.

## Frozen input identity

- Scene/visit: `48018874` / `483945`; TRAIN/HELDOUT: 214/53.
- TRAIN raw Git-blob SHA-256: `167066916ce1a3281ac754dfdeec37ada9f5b0e31227c731c94cebb698a2a6e3`; OID: `a2ddc70775e6d0f9c25f77ef5f869556d83b292c`.
- HELDOUT raw Git-blob SHA-256: `7b65f741e901690f2a723579d75200eebe7b9e77b0cd57c030d4a14d0474c0c7`; OID: `cf28dd385711a31733360e5fc21dce229ce605bc`.
- Git blobs equal the server working copies; ARKitScenes/SplaTAM/rasterizer authorities all match the frozen identities.
- Split identity: `97a707510227271d12859ee78defc0d6170cc24cb67e423568cd1a72e3345dee`; group tuple: `8ad320980bb36edb2accb38629ec3046095c9ef7735fbb748f4e112ee75bd388`.

## Confidence assets, values, and alignment

- All 214 TRAIN and 53 HELDOUT confidence files exist, match manifest timestamps and 192x256 RGB/depth orientation, load deterministically as `uint8`, and contain only values 0/1/2.
- TRAIN value counts: 0=`1240707`, 1=`1188387`, 2=`8089434`.
- TRAIN frames 76 and 79 are genuine checksum-recorded all-zero raw confidence assets. They are not unreadable-file fallbacks; the adapter contains no zero-array fallback.
- The adapter joins confidence from the same manifest row and uses nearest-neighbor resizing.
- The fixed 32-frame identity/dihedral/offset comparison found no nonidentity candidate satisfying the 24/32, +10 percentage-point, official-evidence, and retention requirements. Identity reproduced byte-for-byte in a fresh process (`7565c528e69b74282a47305ddbf662b240a4ee58687ce973baf90b480799b30d`).

## Full-TRAIN geometry

Evaluation mode: all positive-depth pixels, no sampling. One shared M0 registry of `10518528` pixels was used for all masks.

| Mask | Valid pixels | Retention | Median m | p95 m | p99 m | Max m | Geometry |
|---|---:|---:|---:|---:|---:|---:|---|
| M0 | 10518528 | 1.000000 | 0.013919 | 0.129212 | 0.482769 | 6.499599 | FAIL |
| M1 | 9277821 | 0.882046 | 0.012362 | 0.060205 | 0.117651 | 0.673781 | PASS |
| M2 | 8089434 | 0.769065 | 0.011423 | 0.047780 | 0.081353 | 0.367189 | PASS |

The point-to-mesh engine is point-to-triangle surface distance, not nearest vertex. Open3D and independent trimesh R-tree results agree within `8.74346308e-07 m` over 512 points (required <=1e-6 m); all results are finite.

## Supervision structure

| Mask | Retention | Supported frames | Zero-valid frames | Longest unsupported run | Group gate | Structure result |
|---|---:|---:|---:|---:|---|---|
| M1 | 0.882046 | 210/214 (98.13%) | 2 | 4 | FAIL | FAIL |
| M2 | 0.769065 | 210/214 (98.13%) | 4 | 4 | FAIL | FAIL |

The global, frame-fraction, retention, and temporal-run gates pass. The all-eight-group gate fails because groups with fewer than 10 total TRAIN frames cannot supply 10 supported frames. These are preregistered audit design thresholds, not Apple or SplaTAM official thresholds; they were not changed after observing results.

## Tail concentration and attribution

- M0 top 1% registry: `105186` pixels. The smallest frame sets contributing 50/80/90% are `3` / `9` / `18`.
- M0 error >0.30 m: `244571` pixels. Confidence-0 accounts for `98.76%`; confidence-1 for `1.16%`; confidence-2 for `0.08%`.
- M0 >0.30 m ray classes: no mesh hit `21.50%`, sensor behind mesh `11.75%`, sensor in front of mesh `66.75%`.
- No-hit does not dominate M0, so the reference-mesh limitation decision (>50% no-hit and not reduced by confidence filtering) is not met.
- Border bands for M0 >0.30 m: 0-2% `9.07%`, 2-5% `10.96%`, 5-10% `16.57%`, >10% `63.39%`.
- Depth bins: 0-1 m `1.27%`, 1-2 m `55.69%`, 2-3 m `22.38%`, 3-4 m `13.29%`, >4 m `7.37%`.
- Top-20 temporal categories: `{'NO_NEIGHBOR_SUPPORT': 0, 'OCCLUSION_AMBIGUOUS': 11, 'TEMPORALLY_INCONSISTENT': 7, 'TEMPORALLY_SUPPORTED': 2}`. Official poses only were used; HELDOUT and pose optimization were not used.

## Index 78 evidence

Frame 78 / timestamp `653435.595` has `49152` positive-depth pixels and confidence counts `{'0': 49108, '1': 44, '2': 0}`. Its median/p95/p99/max point-to-mesh errors are `0.447075` / `0.686742` / `0.743271` / `0.771408` m. `79.91%` of pixels exceed 0.30 m; within that tail, `92.60%` are sensor-in-front-of-mesh and `7.21%` have no mesh hit. The frame was preserved and not excluded.

## Official SplaTAM zero-mask semantics

- Source audit decision: `FAIL_OFFICIAL_SPLATAM_ZERO_VALID_DEPTH_COMPATIBILITY`.
- Synthetic microtest: `FAIL_ZERO_MASK_MAPPING_DEPTH_MEAN_NONFINITE`.
- Tracking's empty masked sum is finite zero, but mapping's empty masked mean is nonfinite. Initial-frame empty depth also lacks an official skip before empty point-cloud initialization and zero scene-radius calculation.
- Exactly three synthetic forward reductions were used; no real scene, mapper, optimizer, backward, update, or checkpoint was used.

## Cause labels and claim boundary

The top-frame registry uses evidence-bounded multi-label causes: `{'CONFIDENCE_ALIGNMENT_SUSPECT': 0, 'CONFIDENCE_READER_FAILURE': 0, 'CONFIDENCE_ZERO_OR_LOW': 20, 'DYNAMIC_OR_TRANSIENT_SUSPECT': 2, 'IMAGE_BORDER': 9, 'LONG_RANGE': 3, 'MESH_COVERAGE_GAP': 8, 'POSE_INTRINSICS_LOCAL_SUSPECT': 0, 'SENSOR_BEHIND_MESH': 9, 'SENSOR_IN_FRONT_OF_MESH': 11, 'TEMPORAL_INCONSISTENCY': 7, 'UNEXPLAINED': 0}`. `DYNAMIC_OR_TRANSIENT_SUSPECT` is used only when both temporal inconsistency and RGB temporal difference evidence are present; it is not a confirmed dynamic-object label.

Allowed claims are limited to data geometry, confidence-tail association, reference-mesh coverage attribution, and pre-training data-contract qualification. This audit does not show that a learned map exists, that confidence masking improves a trained map, that any frame should be deleted, or that SAFER/FAS-CBF/controller execution occurred.

## Execution counts and integrity

`{"checkpoint": 0, "controller": 0, "download": 0, "environment_creation": 0, "environment_modification": 0, "g0": 0, "learned_map_clearance": 0, "map": 0, "mapper": 0, "nvs": 0, "optimizer_step": 0, "smoke": 0, "training": 0, "variant": 0}`

- GPU execution used by task: 0; the audit ran on CPU.
- Raw assets, canonical manifests, official mesh, PR #71 adapter, SplaTAM authority, environment, masks, poses, intrinsics, and thresholds were not modified.
- No frame was deleted or rerun as a scientific rollout.
- Existing SSH sessions and the persistent reverse-proxy watchdog were not stopped, modified, or rebuilt.

## Final decision

`FINAL_STATUS=NO_ARKITSCENES_METRIC_DEPTH_INPUT_CONTRACT_QUALIFIED`
`FINAL_DECISION=CLOSE_ARKITSCENES_SPLATAM_MAPPING_ROUTE_WITHOUT_TRAINING`
`Only next task=ETH3D_DELIVERY_AREA_LEARNED_3DGS_QUALIFICATION_V1`

Recommendation: no mask. No implementation error or dominant mesh-coverage explanation was established, and none of M0/M1/M2 satisfies all preregistered gates.
