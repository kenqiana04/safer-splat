# Execution Authorization: Formal TUM Splatfacto Training Execution V1R3

The user explicitly and separately authorized **Formal TUM Splatfacto Training
Execution V1R3**. Exactly one frozen configuration, seed `20260716`, and
formal launch are permitted only after every V1R3 gate passes.

## Historical attempt records

- PR #24: `BLOCKED_BY_PROTOCOL_HASH_MISMATCH`, `attempt=0`, reusable=false.
- PR #25: `BLOCKED_BY_GPU_BUSY`, `attempt=0`, reusable=false.
- PR #26: `BLOCKED_BY_EXECUTION_RECORD_PARENT_MISSING`, `attempt=0`,
  reusable=false; neither tmux nor `ns-train` started.

## V1R3 infrastructure correction

Before the three GPU samples, create or verify
`/disk1/zlab/formal_execution_records`, verify it is a writable directory,
create the unique root
`/disk1/zlab/formal_execution_records/tum_fr1_room_splatfacto_v1r3_seed20260716`,
verify it is writable, and write the GPU evidence directly there. This setup
does not consume a training attempt.

## Canonical protocol identity

- protocol commit: `6843fa477adc7f07acdfdb270ad7e4e3349da904`
- command blob / SHA-256: `1650b873e734d8fcdf56b8bc26fff48fdb2730ac` /
  `22d00fadea7eb1fb43556d4690c78113d317c6d144e96b6ad0d294d27a9369a4`
- config blob / SHA-256: `d3e0c104b37304278dd4074787d8781d2281a375` /
  `0d15d8d6fa84049c6b4c34d6fdcaf77114f569c8d22ea9d010ae8144e6c924ea`
- transforms SHA-256:
  `b6a685f4b1a5b2ff3bb9b389c63a138a58119b19dd5cb6d7f671282aeecad29a`

## Attempt boundary

Infrastructure, canonical, environment, data, disk, output, GPU, and CLI
preflight failures consume zero attempts. Attempt count becomes one only after
the tmux session exists, the frozen command is executed, and an `ns-train`
process is observed. No retry, resume, second seed, tuning, SAFER,
navigation, or G1 is authorized.
