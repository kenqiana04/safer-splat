# Formal TUM Splatfacto Training Execution V1R2

## Result

`BLOCKED_BY_EXECUTION_RECORD_PARENT_MISSING`

The canonical protocol, server environment, dataparser-only contract, output
absence, disk capacity, CLI schema, and three fresh physical-GPU-1 samples all
passed. The three samples at 06:34:31Z, 06:35:02Z, and 06:35:32Z had zero
compute processes, 0% GPU utilization, and 6 MiB driver memory; Xorg was the
only graphics process.

Immediately after the third sample, the authorized launch gate tried to create
the required execution-record directory
`/disk1/zlab/formal_execution_records/tum_fr1_room_splatfacto_v1r2_seed20260716`.
Its parent `/disk1/zlab/formal_execution_records` did not exist, so `mkdir`
failed. The gate therefore never created a tmux session or an `ns-train`
process. Attempt count remains **0**. No directory was created to enable a
retry, and no retry, resume, output alteration, evaluation, rendering, SAFER,
or G1 operation was performed.

## Identity and preflight

- Protocol commit: `6843fa477adc7f07acdfdb270ad7e4e3349da904`.
- V1R2 authorization commit: `e44fbdbcda393cd9ab2f63f55d57a0aa922d8e7e`.
- Command/config canonical SHA-256: `22d00fadea7eb1fb43556d4690c78113d317c6d144e96b6ad0d294d27a9369a4` /
  `0d15d8d6fa84049c6b4c34d6fdcaf77114f569c8d22ea9d010ae8144e6c924ea`.
- Transform SHA-256: `b6a685f4b1a5b2ff3bb9b389c63a138a58119b19dd5cb6d7f671282aeecad29a`.
- Environment: Python 3.10.20, Torch 2.1.2+cu118, CUDA 11.8, Nerfstudio 1.1.5,
  gsplat 1.4.0 on physical GPU 1.
- Disk: 510 GiB available; formal output remained absent.

## Scope and follow-up boundary

PR #24 and PR #25 remain immutable attempt-0 blocked records. The V1R2
detached worktree is retained only until this compact evidence is committed and
pushed, then will be removed without touching the formal output or any data.
A future execution requires new explicit authorization; it must not turn this
block into an automatic retry.
