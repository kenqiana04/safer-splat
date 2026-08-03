# Freeze ARKitScenes M1 Empty-Depth-Safe Mapping Handoff V1

## Frozen contract

- M1: `depth_raw > 0 AND confidence >= 1`
- V2 supervision: `PASS_ARKITSCENES_M1_SUPERVISION_V2`
- Zero-valid TRAIN rows: `[76, 79]`; both remain in sequence
- First M1 frame valid pixels: `49152`
- Compatibility module SHA-256: `8930c9d2e5172d0c56e698a418b3f454171e6c9fd84e3079d1f7c3568436a6f3`
- Compatibility Git blob: `b134d45f68f8de060f94f8867dfb173c98be8f0b`
- Official SplaTAM head/source SHA-256: `da6bbcd24c248dc884ac7f49d62e91b841b26ccc` / `b8adb286bea49d6302769ec5af25af4938318044691a8996575c443e4b538816`
- Nonempty synthetic / real forward: `PASS_NONEMPTY_SYNTHETIC_EQUIVALENCE` / `PASS_NONEMPTY_REAL_FRAME_FORWARD_EQUIVALENCE`
- Zero synthetic / real / sequence: `PASS_ZERO_MASK_SYNTHETIC_VALIDATION` / `PASS_ZERO_FRAME_REAL_FORWARD_VALIDATION` / `PASS_SEQUENCE_STATE_DRY_RUN`

## Future execution lock

A future separately authorized task must use the exact TRAIN manifest, M1 mask, compatibility module, official source, GT poses, and empty-depth policy recorded in `downstream_handoff.json`. It must not fall back to M0 or M2, delete/replace frames 76 or 79, or call the mapper an official unmodified baseline.

`FINAL_STATUS=PASS_ARKITSCENES_CONFIDENCE_GE1_SUPERVISION_AND_EMPTY_DEPTH_SAFE_CONTRACT_V2`

`FINAL_DECISION=FREEZE_M1_WITH_EMPTY_DEPTH_SAFE_COMPATIBILITY`

`Only next task=RESUME_ARKITSCENES_SPLATAM_M1_SMOKE_AND_LEARNED_MAP_QUALIFICATION_V1`
