# Cross-Dataset Pre-Freeze Provenance V1

## 1. Purpose

This document records only Cross-Dataset G0 work that occurred before Freeze V1. It adds provenance to the freeze; it does not execute preprocessing, rendering, training, SAFER, or a new experiment.

## 2. Temporal boundary

Replica/TUM work occurred before Freeze V1 on independent historical branches. This revision reads their Git-tracked evidence without checkout, merge, cherry-pick, or replay.

## 3. Replica status

`replica_apartment_0` completed isolated Python 3.9 Habitat-Sim renderer/environment closure, scene load, navmesh, and EGL smoke. The frozen protocol used seed `20260715`, 100 spatial locations, yaw `[0, -60, +60]`, 300 frames, 640x480, HFOV 90, near/far `0.05/20`, camera height `1.50`, and a 270/30 split.

The 300-row manifest SHA-256 is `1056121e4470124e180a3367172440f540f0acdc5adab665c3187ac8ab87be25`. Finite camera-to-world transforms, identity Habitat-to-Nerfstudio/OpenGL conversion, translation scale ratio 1, no auto-scale, no normalization, no COLMAP, and no pose estimation are source-recorded.

Integrity is `blocked_by_rgb_integrity`: 33 RGB frames were black/near-black and 32 depth frames were all zero. No frame was deleted, replaced, resampled, or rerendered; staging was not atomically published. Reconstruction, Splatfacto training, SAFER loader, and SAFER baseline were not started. Replica V1 cannot enter training or G1. Any black-frame diagnosis requires separately authorized Replica V2; V1 must remain unchanged.

## 4. TUM status

`tum_metric_candidate` has source-recorded metric RGB/depth/pose preprocessing and external `transforms.json` contract evidence: 300 deterministic triples, metric scale preservation, no COLMAP pose estimation, and no auto-scale. The formally reported transforms SHA-256 is `b6a685f4b1a5b2ff3bb9b389c63a138a58119b19dd5cb6d7f671282aeecad29a`.

The exact TUM scene identifier is not established by this freeze and remains unresolved. A frozen GSplat checkpoint, SAFER adapter, ellipsoid query, start/goal navigation volume, collision/progress evaluator, and double-integrator wrapper are not ready. TUM remains G0 pending and G1 blocked.

## 5. G0/G1 boundary

G0 covers asset availability, metric/camera protocol, integrity, checkpoint, adapter/query, navigation/evaluator, dynamics, and reproducibility feasibility. G1 is a separately authorized run of the original unmodified SAFER baseline only. Replica and TUM are both ineligible for G1 at this revision.

## 6. Claim boundaries

Renderer output is not generalization. RGB-D preprocessing is not Gaussian reconstruction; reconstruction is not SAFER portability. Failed RGB integrity is not a SAFER baseline failure. TUM transforms provenance is not baseline readiness. Cross-Dataset preprocessing is not method validation.
