# Report: ARKitScenes Confidence-Aware Supervision V2 and Zero-Depth Policy

## Answer

`FINAL_STATUS=PASS_ARKITSCENES_CONFIDENCE_GE1_SUPERVISION_AND_EMPTY_DEPTH_SAFE_CONTRACT_V2`

`FINAL_DECISION=FREEZE_M1_WITH_EMPTY_DEPTH_SAFE_COMPATIBILITY`

This post-audit, pretraining revision freezes M1 with a group-size-normalized supervision gate and a task-owned empty-depth-safe compatibility layer. It preserves PR #72's formal failure. No mapper, optimizer, training, checkpoint, learned map, NVS, clearance, G0, SAFER/FAS-CBF, or controller execution occurred.

## Lineage and frozen input

- Branch/base: `arkitscenes-confidence-ge1-supervision-zero-depth-contract-v2` / `arkitscenes-depth-confidence-p99-tail-audit-v1`
- Base head: `a35ec170aba60de821ecbad56642f092c70df792`
- PR #72: OPEN Draft, unmerged, MERGEABLE/CLEAN, unchanged at `a35ec170aba60de821ecbad56642f092c70df792`
- Scene/visit: `48018874` / `483945`; TRAIN/HELDOUT: 214/53
- TRAIN SHA/blob: `167066916ce1a3281ac754dfdeec37ada9f5b0e31227c731c94cebb698a2a6e3` / `a2ddc70775e6d0f9c25f77ef5f869556d83b292c`
- HELDOUT SHA/blob: `7b65f741e901690f2a723579d75200eebe7b9e77b0cd57c030d4a14d0474c0c7` / `cf28dd385711a31733360e5fc21dce229ce605bc`
- Split/group identities: `97a707510227271d12859ee78defc0d6170cc24cb67e423568cd1a72e3345dee` / `8ad320980bb36edb2accb38629ec3046095c9ef7735fbb748f4e112ee75bd388`
- PR #72 report SHA-256/blob: `e2da3d91085f47fc7716715e05f981d1bd3668794565158da527f65523807149` / `8e1f81350f83235bf2caa7eb5ee4276ff058dda2`

## PR #72 result and V1 diagnosis

PR #72 remains `NO_ARKITSCENES_METRIC_DEPTH_INPUT_CONTRACT_QUALIFIED` / `CLOSE_ARKITSCENES_SPLATAM_MAPPING_ROUTE_WITHOUT_TRAINING`. V1's fixed requirement of 10 supported frames is arithmetically impossible for groups of size 1, 2, and 9. The diagnosis is `PREREGISTERED_FIXED_GROUP_COUNT_GATE_ARITHMETICALLY_INFEASIBLE_FOR_SMALL_GROUPS`; it is not a geometry relaxation and does not make V2 retrospectively preregistered.

## M1 and supervision V2

- M1 definition: `(depth_raw > 0) AND (confidence >= 1)`
- Valid pixels/retention: 9,277,821 / 0.882045567593
- Median/p95/p99/max: 0.012361899950 / 0.060204785317 / 0.117650645971 / 0.673780977726 m
- Global frame support: 210/214 (0.981308411215); unsupported `[76,77,78,79]`
- Zero-valid frames: `[76,79]`; longest unsupported run: 4
- New supported-count formula: `S_g >= max(1, ceil(0.80*N_g))`
- Unchanged gates: global retention >=0.30, support >=90%, longest run <=5, group pixel retention >=0.20
- Fresh-process result: 3 byte-identical runs, SHA-256 `1bc8f179c9a512fcb073a1e6af1ee9272245e242f59a4f78a111d6fc6b190290`

| Group | Hash prefix | N_g | S_g | Required | M0 pixels | M1 pixels | Retention | Unsupported | Pass |
|---:|---|---:|---:|---:|---:|---:|---:|---|---|
| 0 | `35c8aa07359d` | 24 | 24 | 20 | 1179648 | 1125133 | 0.953787062 | none | True |
| 1 | `67dbe5e7997d` | 18 | 18 | 15 | 884736 | 834541 | 0.943265562 | none | True |
| 2 | `f5191466ea0d` | 42 | 38 | 34 | 2064384 | 1646078 | 0.797370063 | 76,77,78,79 | True |
| 3 | `f140bf894637` | 1 | 1 | 1 | 49152 | 43451 | 0.884012858 | none | True |
| 6 | `8c90a2e60f94` | 2 | 2 | 2 | 98304 | 88141 | 0.896616618 | none | True |
| 9 | `4a9afcf310cb` | 24 | 24 | 20 | 1179648 | 1050630 | 0.890630086 | none | True |
| 11 | `8c03ffc28c03` | 9 | 9 | 8 | 442368 | 339631 | 0.767756709 | none | True |
| 12 | `c9da2456432f` | 94 | 94 | 76 | 4620288 | 4150216 | 0.898259156 | none | True |

## Official failure and compatibility behavior

- Official SplaTAM head/source SHA-256: `da6bbcd24c248dc884ac7f49d62e91b841b26ccc` / `b8adb286bea49d6302769ec5af25af4938318044691a8996575c443e4b538816`
- Official source Git blob: `1b082f7e2514da6dbecfacd9a7029c9a0389192b`
- Official all-zero mapping depth mean finite: `False`
- Compatibility SHA-256/blob: `8930c9d2e5172d0c56e698a418b3f454171e6c9fd84e3079d1f7c3568436a6f3` / `b134d45f68f8de060f94f8867dfb173c98be8f0b`
- Official checkout and PR #71 environment remained unmodified.
- First M1 frame valid pixels: `49152`; first-frame empty failure remains `INITIAL_FRAME_ZERO_DEPTH_UNSUPPORTED`.

For later empty frames the frame, RGB, pose, and intrinsics remain present; RGB loss stays finite; depth loss is differentiable exact zero; depth initialization and add-new-Gaussian return zero; no pseudo-depth, frame skip, extra iteration, or state mutation occurs. This is not an official unmodified SplaTAM baseline.

## Qualification results

- Synthetic nonempty: 120 fixed-seed fixtures; f32/f64 max depth diff `0.0`; max gradient diff `0.0`; nonfinite 0.
- Synthetic zero: 4 CPU/GPU dtype cases; exact-zero finite depth and zero finite gradients; official empty mean nonfinite in every case.
- Real nonempty forward-only: 32 frames, all 8 groups; loss/point count/point attributes equivalent; max point diff `0.0`; nonfinite 0; no mutation.
- Real zero forward-only: rows 76 and 79 retain canonical assets, total/RGB finite, depth=0, point/add count=0, correct event, no mutation.
- Sequence dry-run `[74,75,76,77,78,79,80,81]`: order retained, empty-safe only at 76/79, later nonempty path resumes, no state leak.

## Execution and resource boundary

- Synthetic backward count: 244; real backward: 0
- Real forward frame count: 34; state-only sequence frames: 8
- Download/environment create-or-modify/smoke/mapper/optimizer/optimizer step/parameter update/training/checkpoint/learned map/NVS/clearance/G0/controller/SAFER/FAS-CBF: all 0
- Physical GPU 1 final: 6 MiB, 0%, zero compute process, zero task-owned process
- Persistent proxy watchdog: Running/Enabled; pre-existing long-lived SSH PIDs 11964 and 17480 preserved
- sshd/network/firewall changes: 0

## Claim boundary and handoff

The evidence supports only the frozen M1 supervision V2 and bounded compatibility contract. It does not support a learned map, smoke/training success, NVS, navigation, or safety claim. Frames 76/79 cannot be deleted; M0/M2 cannot replace M1; the future mapper role must be `SPLATAM_DERIVED_GT_POSE_MAP_ONLY_WITH_EMPTY_DEPTH_SAFE_COMPATIBILITY`.

Server report: `/disk1/zlab/maintenance_records/arkitscenes_confidence_ge1_supervision_zero_depth_contract_v2/REPORT_REDEFINE_ARKITSCENES_CONFIDENCE_AWARE_SUPERVISION_CONTRACT_V2_AND_ZERO_DEPTH_FRAME_POLICY_V1.md`

Handoff: `FREEZE_ARKITSCENES_M1_EMPTY_DEPTH_SAFE_MAPPING_HANDOFF_V1.md`

`Only next task=RESUME_ARKITSCENES_SPLATAM_M1_SMOKE_AND_LEARNED_MAP_QUALIFICATION_V1`
