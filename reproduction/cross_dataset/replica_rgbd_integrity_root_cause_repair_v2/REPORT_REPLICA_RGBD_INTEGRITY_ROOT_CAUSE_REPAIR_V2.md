# REPORT: Replica RGB-D Integrity Root-Cause, Qualified Repair and Atomic Publication V2

## 1. Research question and historical identity

This task diagnosed why frozen Replica RGB-D V1 contained black/near-black RGB
and zero-depth frames. The source authority is historical commit
`fe250df543aa158557c176ee4f87dc131bb61e60` (not an ancestor of PR #51).
Recovered source blobs include the V1 renderer
`8d59eb5b0d7434be76c8b385c97ee0d7e5dcfaa4` and the exact integrity checker
`cae67b3be07c1b801dc7af51ebc0ffcc6bbe6efb`.

## 2. Frozen renderer, scene and protocol

The unchanged renderer is Python 3.9.23, Habitat-Sim 0.3.3, physical RTX 4090
GPU 1 / in-process CUDA device 0. The scene remains `apartment_0`. The mesh
SHA-256 is `274677d9b7caa413230363b68f4aa472e5cc1afe87e422a489fa1b7d844c6182`,
the navmesh SHA-256 is `32296d6457d3855ffe172cf1970364559def5dd15892e149b44d0bc7c6b7e938`,
and the 32-texture inventory was read-only hashed.

The immutable manifest is
`/disk1/zlab/cross_dataset_assets/manifests/replica_protocol_v1/formal_camera_manifest.csv`,
SHA-256 `1056121e4470124e180a3367172440f540f0acdc5adab665c3187ac8ab87be25`.
It remains 100 locations × yaw order 0/-60/+60 = 300 frames, 640×480 pinhole,
HFOV 90, near/far 0.05/20 m, height 1.50 m and a disjoint 270/30 split.
V1 transforms remain framewise identical to the manifest, with no scale,
normalization, COLMAP or pose-estimation operation.

## 3. Preserved V1 staging and re-audit

The read-only evidence directory is
`/disk1/zlab/cross_dataset_assets/processed/replica/apartment_0.rendering`.
Its 610-file inventory tree SHA-256 is
`39367c04f6e6ea510590f77ee1275e78333123608e6eb2223c1d419260288c51`.
No V1 file was deleted, renamed, overwritten, repaired, or published.

The recovered V1 thresholds are RGB shape `(480,640,3)`, `max>0` and
`fraction(rgb>0)>0.01`; depth shape `(480,640)`, `uint16` and `max>0`.
They reproduce 33 RGB failures and 32 depth failures. The intersection is 32;
the only RGB-only frame is `frame_0034`; there is no depth-only frame.

## 4. Pattern and isolated evidence

The 33 anomalies occupy 23 locations and all three yaw values (-60: 14,
0: 9, +60: 10); 27 are train and 6 eval. There are short local runs at
30–31, 42–43, 75–76, 180–181, 189–191, 270–271 and 273–275, rather than a
single yaw, split, or end-of-run pattern.

Before any diagnostic rendering, an 81-frame registry was frozen: every
historical anomaly, normal yaws at those locations where available, and 12
deterministically selected normal controls. The full serial diagnostic replay
ran exactly once for all 300 poses and produced 33 in-memory failures and 33
post-save failures. Thus PNG/depth serialization is not the cause.

Every frozen probe then ran in a fresh Python subprocess and fresh Simulator
twice (A/B). All 33 historical anomalies remained invalid in-memory and
post-save in both repetitions, while the registry results were deterministic.
The defect is therefore not caused by a long-lived process or buffer state.

## 5. Sensor and pose/geometry diagnosis

Both configured sensors are the frozen pinhole RGB UUID `rgba` and depth UUID
`depth`, at 480×640 internally, HFOV 90, near 0.05, far 20 and [0,1.5,0]
attachment; a valid control produced both RGB and metric depth. All 300 pose
matrices are finite, orthogonal with determinant one, apply the 1.50-m height
offset, use navigable source points, and lie in the finite scene bounds.

Fresh actual renderer observations still fail at the same 33 frozen poses.
That is equivalent direct coverage evidence: a static scene asset/texture
coverage limitation remains after serialization, process lifetime, sensor
attachment and pose-geometry alternatives are excluded.

## 6. Root cause, repair gate and V2 status

`PRIMARY_ROOT_CAUSE = SCENE_ASSET_OR_TEXTURE_COVERAGE_DEFECT`.
There are no secondary findings. This is not one of the three authorized V2
repairs (serialization, long-lived renderer state, or sensor attachment), so
the repair contract is `NOT_AUTHORIZED_DUE_TO_ROOT_CAUSE_GATE` and protocol
fields changed is empty.

Formal V2 render count is 0; V2 RGB/depth bad, missing and extra counts are
not applicable; transforms and split preservation apply only to the preserved
V1 identity. No V2 dataset identity, no V2 output, and no atomic publication
were created. Publication status is `NOT_AUTHORIZED_DUE_TO_V2_INTEGRITY_GATE`.

## 7. Boundary and handoff

Gaussian training count, SAFER execution count, CBF-QP count, Start-Safe,
Risk-Aware and Recovery/V4-C counts, and TUM rollout count are all zero.
The paused paired20 manifest remains SHA-256
`380717f0ec39e0e422902573685f5a2838e78dd6efcce500ba71585efd3d82f6`.
RGB-D integrity is not a Gaussian-map qualification.

Final status: `BLOCKED_BY_REPLICA_SCENE_ASSET_RENDER_COVERAGE_DEFECT`.
The sole recommended next task is `REPLICA_SCENE_ASSET_COVERAGE_AUDIT_V1`.
