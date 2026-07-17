# Formal TUM Splatfacto Training Execution V1R3

## Result

`BLOCKED_BY_LAUNCH_WRAPPER` with `attempt_count=0`.

V1R3 corrected the prior ordering issue: `/disk1/zlab/formal_execution_records`
and the unique writable V1R3 record root were created before all GPU sampling.
Canonical protocol identity, environment, dataparser-only 300/240/60 checks,
output absence, 506 GiB free disk, CLI schema, and three fresh GPU-1 samples
passed. The samples at 12:40:43Z, 12:41:13Z, and 12:41:43Z each had zero CUDA
compute processes, 0% utilization, and 6 MiB driver memory.

Immediately after T0, the pre-created tmux wrapper invoked the exact frozen
training script. The script exited at 12:41:44Z with code 1 before `ns-train`
appeared: its conda activation path ran
`deactivate-gfortran_linux-64.sh`, which referenced an unbound `GFORTRAN`
variable under the frozen script's `set -u`. No formal output, checkpoint,
evaluation, render, or training process was created. No retry, resume, tuning,
second seed, SAFER, navigation, or G1 action occurred.

## Identity and boundary

- PR #24/#25/#26 remain immutable Draft blocked records, each attempt 0.
- V1R3 authorization commit: `44d3c821e4036970c976d880703f50cf03a364f6`.
- Protocol commit: `6843fa477adc7f07acdfdb270ad7e4e3349da904`.
- Command/config SHA-256:
  `22d00fadea7eb1fb43556d4690c78113d317c6d144e96b6ad0d294d27a9369a4` /
  `0d15d8d6fa84049c6b4c34d6fdcaf77114f569c8d22ea9d010ae8144e6c924ea`.
- Transforms SHA-256:
  `b6a685f4b1a5b2ff3bb9b389c63a138a58119b19dd5cb6d7f671282aeecad29a`.
- Environment: zlab-Super-Server, Python 3.10.20, Torch 2.1.2+cu118, CUDA
  11.8, Nerfstudio 1.1.5, gsplat 1.4.0, GPU UUID
  `GPU-78ef17e4-66cc-4a58-fe43-67d31be8981d`.

The server record root is retained. The detached V1R3 worktree will be removed
only after this compact evidence is committed, pushed, and copied. A future
attempt needs new explicit authorization; this result does not allow G0, G1,
or automatic SAFER work.
