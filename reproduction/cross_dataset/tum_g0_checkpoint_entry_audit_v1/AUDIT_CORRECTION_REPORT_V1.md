# TUM Depth-Scale and Dataparser Audit Correction V1

## Corrected Findings

The original `RuntimeError` comparing tensor dimensions 3 and 4 occurred in audit post-processing after dataparser output generation.
The corrected native-shape identity check passed for transform `[3, 4]` with maximum error `0.0`.
Train/validation parsing completed with `240/60` frames; total `300`, drop `0`.
All `300` poses mapped to source frames. Actual translation-ratio median is `1.0` (range `0.9999999586992355` to `1.0000000374593834`).

## Depth Contract Closure

Official source: https://cvg.cit.tum.de/data/datasets/rgbd-dataset/file_formats
Page SHA-256: `042bd173d28ed47caff54e8ec92a66a622ec0573c13d73cd2e348dc092b5daad`.
Depth is 640x480 16-bit monochrome PNG; `5000` units/m gives meter scale `0.0002`.
Zero means `missing_value_or_no_data`. Freiburg 1 correction `1.035` was already applied and is not reapplied.
`300/300` selected depth files are byte-identical to raw mappings; mismatch count is `0`.
Historical preprocessing used `shutil.copy2` and neither scaled nor re-encoded depth.
Nerfstudio default is `0.001`; future training must explicitly set `--pipeline.datamanager.dataparser.depth-unit-scale-factor 0.0002`.

## Cache Validation Scope Correction

The frozen base already tracks `21` core `__pycache__/*.pyc` files. They predate this task and were not removed, modified, or regenerated.
Baseline-aware validation finds set difference `0`, cache diff `0`, audit tracked cache `0`, and audit untracked cache `0`.
The former repository-wide empty-cache rule was over-broad; this task instead proves no cache was introduced or changed.

## Boundary and Decision

No transforms or depth PNGs were modified. No preprocessing, model, trainer, optimizer, viewer, training, checkpoint, SAFER, navigation, or G1 execution occurred.
Decision: **`PASS_DEPTH_AND_DATAPARSER_CORRECTION`**. G0-D/G0-H/G0-I are passed. Global G0 is `partial_ready`; checkpoint-entry decision is `READY_FOR_FORMAL_SPLATFACTO_TRAINING_PREREGISTRATION`.
Correction preregistration `1f15ad20999ebc4b21cb628fc2866b1fc7742bb8` is an independent Git commit preceding correction execution: `True`.
This permits only Formal TUM Splatfacto Training Protocol Preregistration, not checkpoint readiness. `G1_allowed=false` remains binding.
