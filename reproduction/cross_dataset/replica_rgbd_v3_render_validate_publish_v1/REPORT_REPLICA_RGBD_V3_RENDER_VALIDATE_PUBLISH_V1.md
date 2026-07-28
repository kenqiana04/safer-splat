# Replica RGB-D V3 Formal Render, Validation, and Atomic Publication

**FINAL_STATUS:** `PASS_REPLICA_RGBD_V3_RENDER_VALIDATE_AND_ATOMICALLY_PUBLISH`

## Frozen protocol and rationale
PR #54 head is `1b8fabb504235774885e40e28bd2ea83032a1bb8`. Contract, manifest CSV/JSON, transforms, pose-array, registry, and split identities were copied byte-for-byte before rendering. This task is intentionally separate from pre-render qualification: all 300 formal RGB-D frames were freshly produced here, not copied from preprobe observations.
Historical renderer commit/blob: `fe250df543aa158557c176ee4f87dc131bb61e60` / `8d59eb5b0d7434be76c8b385c97ee0d7e5dcfaa4`. The frozen saving contract is RGB uint8 RGB PNG after alpha removal and depth uint16 millimetre PNG with decode scale 0.001 m. Scene identity remains direct `mesh.ply` `274677d9b7caa413230363b68f4aa472e5cc1afe87e422a489fa1b7d844c6182` and original navmesh `32296d6457d3855ffe172cf1970364559def5dd15892e149b44d0bc7c6b7e938`; no semantic or diagnostic mesh was substituted.

## Formal render and integrity
The serial schedule rendered 100 locations and 300 frames with 100 fresh subprocesses and 100 fresh Simulators. Terminal-valid/integrity-failure/infrastructure-failure: 300/0/0; infrastructure retries: 0.
Disk RGB/depth counts are 300/300. V1 RGB/depth bad counts are 0/0; V3 RGB/depth threshold failures are 0/0. Missing/extra/duplicate/pairing errors are 0/0/0/0.
Minimum formal RGB/depth coverage is 0.100700/0.100700; preprobe-compared frames 300, preprobe-pass/formal-fail 0. Memory-disk RGB/depth mismatch counts are 0/0.

## Identity, double validation, and publication
Train/eval remains 90/10 locations and 270/30 frames with no leakage. Pose identity passed=PASS; no auto-scale, normalization, COLMAP, pose estimation, coordinate refit, or camera replacement. Validation A/B both passed with disagreement count 0.
Staging RGB/depth/metadata/complete tree SHA values are `d05a9fe3820cbbe019ab9891d0c13f9204254d49e910179c2d4326e38d4a57a4`, `707e6a8359e66e89bc72d7ee400a146fd86275274b7485359f3e2d85fc71b920`, `68dedb92ad8afcd76c491dcd217df4e6aebf27624238c1eb3f92f4d5155b9efc`, `60a9e0b517ba8e305c4b7ff010bb330c1e38c422c66899398129cce741a06bd0`. Same-filesystem temporary copy, fsync, byte-for-byte rehash, and atomic rename passed. Published target `/disk1/zlab/cross_dataset_assets/processed/replica/apartment_0.rendering_v3` content tree SHA is `60a9e0b517ba8e305c4b7ff010bb330c1e38c422c66899398129cce741a06bd0`; complete target tree SHA is `24e21d3bccceb0516ed8b9b49b426964f3954ccd0cd804eedd5846baabd66dcb`.
Dataset identity declares V3 is not a V1 repair, no frame replacement, no threshold change, no V1 reuse, no training, and no SAFER. Gaussian training, SAFER/CBF, Start-Safe/Risk-Aware/Recovery, and TUM rollout counts are all zero; paired20 remains `380717f0ec39e0e422902573685f5a2838e78dd6efcce500ba71585efd3d82f6`.

## Claim boundary and next task
Published RGB-D data is not Gaussian mapping qualification, SAFER query qualification, navigation baseline qualification, or FAS-CBF validation.

**Only next task:** `REPLICA_RGBD_GAUSSIAN_MAPPING_FRONTEND_QUALIFICATION_V1`
