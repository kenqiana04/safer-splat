# ARKitScenes V1 Split Failure Audit

PR67_FORMAL_STATUS=BLOCKED_BY_ARKITSCENES_DATA_OR_COORDINATE_CONTRACT

SCIENTIFIC_INTERPRETATION=BLOCKED_BY_FIXED_240_60_SPATIAL_GROUP_SPLIT_CONTRACT

- PRIMARY `42899163` has `N=173`; the immutable V1 minimum `TRAIN>=220` plus `HELDOUT>=50` needs at least 270 frames and is mathematically impossible.
- BACKUP `48018874` has `N=267`; the same immutable 220/50 total lower bound is mathematically impossible.
- V1 first searched an exact complete-group `TRAIN=240` subset. Even when such a subset exists, at most `267-240=27` frames remain, so an exact complete-group `HELDOUT=60` subset cannot exist.
- Therefore V1 `HELDOUT=0` follows from allocation order and the fixed integer contract. It does not prove that independently held-out spatial groups do not exist.

This audit does not modify PR #67, candidates, data, keyframes, groups, or any mapping/geometry result. Split protocol only: no mapping training; no geometry result.
