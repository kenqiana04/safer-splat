# REPORT: TUM Remaining G0 Checkpoint-Entry Audit V1

## Executive Summary

The authoritative audit ran on `zlab-Super-Server` (4090) against the immutable
TUM root `/disk1/zlab/cross_dataset_assets`. The exact sequence is
`rgbd_dataset_freiburg1_room` (`TUM_FR1_ROOM`). The frozen transforms file is
`/disk1/zlab/cross_dataset_assets/processed/tum_rgbd/freiburg1_room/transforms.json` and its SHA-256 matches the frozen
value: `b6a685f4b1a5b2ff3bb9b389c63a138a58119b19dd5cb6d7f671282aeecad29a`. All 300 selected RGB, depth, and pose records
were read on the server; structural integrity, pairing, rigid-pose checks, and
source pre/post hashes passed. The formal decision is
**`BLOCKED_BY_CRITICAL_PROVENANCE`**, with additional
**`BLOCKED_BY_DATAPARSER`** evidence. No training, checkpoint, SAFER loader,
baseline, navigation, or G1 execution occurred.

## Execution Environment Correction

Stage 0 preregistration was committed in the Windows Git workspace. Windows is
orchestration-only; its preliminary local probe was superseded and was not used
for any gate. Data, CUDA, Nerfstudio, gsplat, PyTorch, and dataparser evidence
comes only from the 4090 server: conda `safer_splat_official`, Python
`3.10.20 (main, Jun 11 2026, 15:17:37) [GCC 14.3.0]`, PyTorch `2.1.2+cu118`, CUDA
`11.8`, Nerfstudio `1.1.5`, gsplat
`1.4.0`, and visible GPU `NVIDIA GeForce RTX 4090`.

## Data and Geometry Results

- Remote raw root: `/disk1/zlab/cross_dataset_assets/raw/tum_rgbd/rgbd_dataset_freiburg1_room`
- Processed frames: 300 RGB, 300 depth, 300 poses.
- RGB: `pass_structural`; all-zero `0`, duplicate `0`.
- Depth: `pass_structural_unit_pending`; all-zero `0`, nonfinite `0`.
- Pairing: `pass`, no reassociation; maximum historical RGB-depth offset `0.017915010452270508` s.
- Pose/intrinsics/transforms: required fields present and preregistered rigid tolerances audited from the server file.
- Source raw metadata hashes were unchanged before/after audit: `True`.

## Metric Scale and Dataparser

Depth scale is not guessed: the frozen preprocessor copies depth PNGs and the
frozen transforms omit `depth_unit_scale_factor`. Consequently the raw unit and
meter conversion are not source-established (`BLOCKED_BY_CRITICAL_PROVENANCE`).

The server-only dataparser API audit used `orientation_method=none`,
`center_method=none`, and `auto_scale_poses=false`, without model, optimizer,
trainer, viewer, or checkpoint. It raised `RuntimeError('The size of tensor a (3) must match the size of tensor b (4) at non-singleton dimension 0')`. No fallback
to `ns-train` or training was attempted, so frame-drop and parsed/source
translation-ratio are unresolved.

## Splatfacto and SAFER Boundary

`ns-train --help` and `ns-train splatfacto --help` returned zero on the server.
The command artifact is a non-executed contract only; formal split/seed/output
settings and all training hyperparameters remain pending separate preregistration.
`training_iterations_executed=0` and `checkpoint_created=false`.

The SAFER review is `static_source_contract_only`: expected attributes are means,
scales, quaternion rotations, opacities, and colors/SH. Its result is not a
loader pass and cannot validate a nonexistent TUM checkpoint.

## Gate Decision and Next Step

Data structural gates are supported by the 4090 evidence, but global G0 remains
`blocked`; `formal_checkpoint_exists=false`, `safer_loader_validated=false`, and
`G1_allowed=false`. Formal TUM Splatfacto Training Protocol Preregistration is
not yet authorized. The next task must first establish a source-backed depth
unit/scale contract and resolve the dataparser shape failure without training.
G1 SAFER baseline remains forbidden.
