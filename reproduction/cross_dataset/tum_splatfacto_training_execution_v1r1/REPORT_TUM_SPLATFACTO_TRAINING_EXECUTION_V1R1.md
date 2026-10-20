# REPORT: Formal TUM Splatfacto Training Execution V1R1

## Executive Summary

The user authorized one formal TUM_FR1_ROOM Splatfacto attempt on the
authoritative 4090. The attempt was not launched: all three required GPU 1
pre-launch samples contained the same unrelated Python compute process. The
valid outcome is `BLOCKED_BY_GPU_BUSY`; attempt count remains zero.

## Identity and preflight

- Dependency: Draft PR #23 at protocol commit `6843fa477adc7f07acdfdb270ad7e4e3349da904`.
- Previous PR #24 remains immutable blocked evidence with attempt count zero.
- V1R1 authorization commit: `1f575b17206da2056b968d9e2c03d5bf36160765`.
- Server/worktree: `zlab-Super-Server` / `/disk1/zlab/formal_execution_worktrees/tum_splatfacto_training_execution_v1r1`.
- Command blob/canonical/checkout SHA: `1650b873e734d8fcdf56b8bc26fff48fdb2730ac` / `22d00fadea7eb1fb43556d4690c78113d317c6d144e96b6ad0d294d27a9369a4` / `22d00fadea7eb1fb43556d4690c78113d317c6d144e96b6ad0d294d27a9369a4`.
- Config blob/canonical/checkout SHA: `d3e0c104b37304278dd4074787d8781d2281a375` / `0d15d8d6fa84049c6b4c34d6fdcaf77114f569c8d22ea9d010ae8144e6c924ea` / `0d15d8d6fa84049c6b4c34d6fdcaf77114f569c8d22ea9d010ae8144e6c924ea`.
- Environment, CLI schema, dataparser-only 300/240/60 check, transforms hash, output absence, and 509.49 GiB disk check passed.

## Blocked launch

GPU UUID was `GPU-78ef17e4-66cc-4a58-fe43-67d31be8981d`. Samples at
`05:29:21Z`, `05:30:08Z`, and `05:30:59Z` each showed PID `2638791` (`python`)
using 1728 MiB. It was not killed, paused, or moved. No tmux session, execution
record root, formal run directory, checkpoint, log, evaluation, rendering, or
SAFER action was created.

## Result and boundary

`validator_status = BLOCKED_BY_GPU_BUSY`. No tuning, resume, retry, second seed,
SAFER, navigation, or G1 occurred; `G1_allowed=false`. The only possible future
task remains a separately authorized V1R1 execution with a new preflight and an
idle GPU; G0 is not available because no checkpoint candidate exists.
