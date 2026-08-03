# REDEFINE_ARKITSCENES_CONFIDENCE_AWARE_SUPERVISION_CONTRACT_V2_AND_ZERO_DEPTH_FRAME_POLICY_V1

## Classification

`POST_AUDIT_PRETRAINING_PROTOCOL_REVISION`

This protocol preserves PR #72's formal fail-closed result. It does not reinterpret that audit as a pass. It evaluates exactly one previously measured candidate, M1 (`depth_raw > 0 AND confidence >= 1`), under a group-size-normalized supervision gate and qualifies a task-owned empty-depth compatibility branch before any future mapper execution.

## Frozen scientific input

- Scene / visit: `48018874` / `483945`
- TRAIN / HELDOUT rows: `214` / `53`
- PR #72 head: `a35ec170aba60de821ecbad56642f092c70df792`
- TRAIN raw SHA-256: `167066916ce1a3281ac754dfdeec37ada9f5b0e31227c731c94cebb698a2a6e3`
- HELDOUT raw SHA-256: `7b65f741e901690f2a723579d75200eebe7b9e77b0cd57c030d4a14d0474c0c7`
- Split identity: `97a707510227271d12859ee78defc0d6170cc24cb67e423568cd1a72e3345dee`
- Selected group tuple: `8ad320980bb36edb2accb38629ec3046095c9ef7735fbb748f4e112ee75bd388`

## Supervision V2

The unchanged gates are:

- global M1/M0 pixel retention >= 0.30;
- at least 90% of all 214 TRAIN frames supported;
- frame support means `M1_valid >= max(1024, 0.05 * M0_positive)`;
- longest consecutive unsupported run <= 5;
- per-group M1/M0 pixel retention >= 0.20.

The only revised gate is group supported-frame count. For group size `N_g` and supported count `S_g`:

`S_g >= max(1, ceil(0.80 * N_g))`

No floor, exemption, regrouping, frame deletion, HELDOUT supplementation, alternative confidence threshold, or result-dependent gate change is permitted.

## Empty-depth policy

The future mapper role, if separately authorized after this qualification, is:

`SPLATAM_DERIVED_GT_POSE_MAP_ONLY_WITH_EMPTY_DEPTH_SAFE_COMPATIBILITY`

For nonempty M1 frames, the official loss and depth-point paths are delegated without semantic change. For a later zero-valid frame, the frame/RGB/pose/intrinsics remain present, RGB supervision remains active, the depth loss is a differentiable exact zero, and no depth initialization or new Gaussian addition occurs. No pseudo-depth, neighbor-depth substitution, frame skip, compensation iteration, or parameter mutation is allowed. A zero-valid first frame terminates as `INITIAL_FRAME_ZERO_DEPTH_UNSUPPORTED` and cannot trigger automatic frame replacement.

## Execution boundary

Real mapper loops, optimizers, optimizer steps, parameter updates, training, checkpoints, learned maps, NVS, clearance checks, G0, controller benchmarks, and SAFER/FAS-CBF execution are forbidden. Synthetic backward is allowed only for the isolated gradient contract. Real TRAIN frames are forward-only.
