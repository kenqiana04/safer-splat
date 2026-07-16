# TUM Remaining G0 Checkpoint-Entry Audit V1: Protocol Preregistration

## Scope and immutable baseline

- Base branch: `experiment-protocol-freeze-v1`
- Base commit: `0fb8698e8590aead60032487fc3321c07f2fd99c`
- Target dataset identifier: `tum_metric_candidate`
- Frozen TUM G0 status: `pending`
- Frozen TUM G1 permission: `false`
- Expected external `transforms.json` SHA-256:
  `b6a685f4b1a5b2ff3bb9b389c63a138a58119b19dd5cb6d7f671282aeecad29a`
- Historical evidence branch/commit:
  `safer-cross-dataset-metric-preprocessing` /
  `3e22a7cae6f4c3c2c192cc2d7af3c9fbd607a0a3`
- Historical report:
  `work/risk_aware_cbf/REPORT_CROSS_DATASET_METRIC_PREPROCESSING.md`
- Expected historical-report SHA-256:
  `ff0f43a4465faf76cb18bd77e044a4662b0f51dbcfc65277813689db80af4bd1`

The five Freeze V1 provenance files are read-only inputs. This audit must not
modify core code, the Freeze V1 directory, historical evidence, source RGB,
source depth, pose files, `transforms.json`, checkpoints, or trial results.

## Explicitly excluded work

No `ns-train` training invocation, optimizer/model construction, forward or
backward pass, viewer, checkpoint write, SAFER loader execution, SAFER baseline,
navigation trial, data download, preprocessing, reassociation, resampling,
replacement, deletion, or source-asset modification is permitted.

## Preregistered gates

| Gate | Fixed question | Pass evidence | Stop condition |
| --- | --- | --- | --- |
| G0-A | Dataset identity and source provenance | One exact identity is supported by historical and current source evidence | unresolved or conflicting identity |
| G0-B | Asset reachability and immutability | Source RGB, depth, pose, association, intrinsics, and transforms are present, readable, inventoried, and unchanged | unavailable asset or transforms hash mismatch |
| G0-C | RGB integrity | Every expected RGB file decodes, is nonempty, has consistent shape, and has no all-zero image or missing frame | structural RGB failure |
| G0-D | Depth integrity | Every expected depth file decodes, is nonempty, has finite values and positive finite depth; unit and scale have source support | structural depth failure or unresolved unit/scale |
| G0-E | RGB/depth/pose pairing | 300 actual, unique, ordered pairs and poses are verifiable without reassociation | missing, duplicate, unordered, or mismatched pair |
| G0-F | Camera intrinsics contract | Required intrinsics are explicit, finite, positive where applicable, and frame-compatible | missing or invalid intrinsics |
| G0-G | Pose convention and rigid-transform validity | Every transform is finite 4x4 camera-to-world-compatible rigid geometry | invalid transform or unresolved convention |
| G0-H | Metric scale preservation | Source evidence rules out COLMAP, auto-scale, and pose normalization; scale/unit are traceable | metric scaling or provenance conflict |
| G0-I | Nerfstudio transforms/dataparser compatibility | Safe environment/schema evidence shows the immutable transforms contract can be parsed without silent frame or pose-scale changes | environment/dataparser blocker |
| G0-J | Splatfacto command-entry feasibility | `ns-train splatfacto --help` supports an explicit non-executed command template and all required options are source-supported | missing executable or unsupported required contract |
| G0-K | Standard checkpoint to SAFER loader static compatibility | Static code contract is recorded without executing a loader | unresolved/incompatible static contract blocks SAFER, not this training-entry substage |
| G0-L | Reproducibility and environment provenance | OS, Python, packages, command evidence, source hashes, and bundle hash are captured | critical provenance conflict |

## Fixed numerical and structural rules

The following tolerances are fixed before inspection and may not be changed:

- `max(abs(R.T @ R - I)) <= 1e-5`
- `abs(det(R) - 1) <= 1e-5`
- `max(abs(bottom_row - [0, 0, 0, 1])) <= 1e-8`

No historical numeric black-frame or near-black threshold is frozen in the
read-only provenance. Therefore `threshold_not_previously_frozen` applies:
near-black is descriptive only and cannot make an RGB gate fail or pass. The
only RGB rejection rules are decode failure, zero-byte file, missing frame,
shape mismatch, nonfinite data where applicable, and a wholly zero image. The
only depth rejection rules are decode failure, zero-byte file, missing frame,
shape mismatch, nonfinite depth, wholly zero depth, lack of positive finite
depth, or unresolved source-supported unit/scale. A new numeric threshold would
require a separate formal threshold preregistration.

## Decision states and stopping rules

The only final checkpoint-entry decisions are:

- `READY_FOR_FORMAL_SPLATFACTO_TRAINING_PREREGISTRATION`
- `BLOCKED_BY_DATASET_IDENTITY`
- `BLOCKED_BY_ASSET_UNAVAILABLE`
- `BLOCKED_BY_ASSET_HASH_MISMATCH`
- `BLOCKED_BY_RGB_INTEGRITY`
- `BLOCKED_BY_DEPTH_INTEGRITY`
- `BLOCKED_BY_PAIRING`
- `BLOCKED_BY_INTRINSICS`
- `BLOCKED_BY_POSE_CONTRACT`
- `BLOCKED_BY_METRIC_SCALE`
- `BLOCKED_BY_NERFSTUDIO_ENVIRONMENT`
- `BLOCKED_BY_DATAPARSER`
- `BLOCKED_BY_SPLATFACTO_ENTRY_CONTRACT`
- `BLOCKED_BY_CRITICAL_PROVENANCE`
- `FAIL`

Identity conflict, source-asset unavailability, a transforms hash mismatch,
structural integrity failure, unverified depth scale, invalid rigid transform,
metric-scale change, unsafe dataparser behavior, required environment change,
or validator failure stops checkpoint-entry adjudication. The audit then records
the blocker without repairing data or continuing to training.

Even a ready result means only that a separate *Formal TUM Splatfacto Training
Protocol Preregistration* may be proposed. It never means that a checkpoint
exists, reconstruction quality is known, SAFER is validated, global G0 passed,
or G1 is allowed. `G1_allowed` remains false.
