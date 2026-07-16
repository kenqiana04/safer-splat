# REPORT: TUM Remaining G0 Checkpoint-Entry Audit V1

## Executive Summary

The authoritative correction ran on `zlab-Super-Server` in `/disk1/zlab/conda_envs/safer_splat_official` against immutable TUM assets `/disk1/zlab/cross_dataset_assets`.
Sequence `rgbd_dataset_freiburg1_room` (`TUM_FR1_ROOM`) uses frozen transforms SHA-256 `b6a685f4b1a5b2ff3bb9b389c63a138a58119b19dd5cb6d7f671282aeecad29a`.
Final correction decision: **`PASS_DEPTH_AND_DATAPARSER_CORRECTION`**. Checkpoint-entry decision: **`READY_FOR_FORMAL_SPLATFACTO_TRAINING_PREREGISTRATION`**.

## Depth-Scale and Dataparser Correction

The original 3-vs-4 error was an audit post-processing comparison bug, not a dataparser generation failure.
Corrected native transform shape `[3, 4]` is identity `True` with max error `0.0` and parser scale `1.0`.
Dataparser train/val counts are `240/60`; total `300`, frame drop `0`, unmatched poses `0`.
Actual parsed/source translation-ratio median `1.0`; no orientation or centering change and auto scale is `False`.
Official TUM depth evidence `https://cvg.cit.tum.de/data/datasets/rgbd-dataset/file_formats` SHA-256 `042bd173d28ed47caff54e8ec92a66a622ec0573c13d73cd2e348dc092b5daad` confirms 640x480 16-bit monochrome PNG, 5000 units/m, meter scale `0.0002`, and zero `missing_value_or_no_data`.
Freiburg 1 `1.035` is pre-applied. `300/300` processed selected depths are byte-identical raw copies; mismatches `0`.
Historical preprocessor `shutil.copy2` does not scale depth. Double scaling risk is `False`.
Installed Nerfstudio default `0.001` differs from required `0.0002`; future separately preregistered training must use `--pipeline.datamanager.dataparser.depth-unit-scale-factor 0.0002` exactly once.

## Cache Validation Scope Correction

The frozen base contains `21` already tracked core cache files. Removing them would violate the core-path restriction, so they are baseline evidence rather than a task failure.
Relative to base, tracked cache set difference is `0`, tracked cache diff count is `0`, and this audit directory has `0` tracked and `0` untracked cache files.
Validator policy is baseline-aware: no task-introduced, modified, or deleted cache is allowed.

## Gate and Scope Boundary

G0-D depth integrity: passed. G0-H metric scale: passed. G0-I dataparser: passed.
Global G0: `partial_ready`. `formal_checkpoint_exists=false`, `training_iterations_executed=0`, `checkpoint_created=false`, `safer_loader_validated=false`, `navigation_gates_completed=false`, `G1_allowed=false`.
No TUM source asset, transforms, or depth PNG was modified. No preprocessing, training, checkpoint, SAFER execution, or G1 work occurred.
Correction preregistration commit `1f15ad20999ebc4b21cb628fc2866b1fc7742bb8` precedes correction execution: `True`.
Training preregistration readiness is not checkpoint readiness. G1 SAFER baseline remains forbidden.
