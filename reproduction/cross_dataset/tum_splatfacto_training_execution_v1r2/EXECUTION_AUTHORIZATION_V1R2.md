# Execution Authorization: Formal TUM Splatfacto Training Execution V1R2

The user explicitly and separately authorized **Formal TUM Splatfacto Training
Execution V1R2**. One frozen command, seed `20260716`, and formal start are
permitted only after every V1R2 preflight gate passes.

## Non-reusable predecessor records

- `execution_pr_24_status = BLOCKED_BY_PROTOCOL_HASH_MISMATCH`
- `execution_pr_24_attempt_count = 0`
- `execution_pr_24_reusable = false`
- `execution_pr_25_status = BLOCKED_BY_GPU_BUSY`
- `execution_pr_25_attempt_count = 0`
- `execution_pr_25_reusable = false`

## Stale-process cleanup precedent

- `pid = 2638791`
- `cleanup_status = STALE_SPLATNAV_PROCESS_TERMINATED_GPU_1_IDLE`
- `maintenance_record = /disk1/zlab/maintenance_records/stale_splatnav_pid_2638791_cleanup`
- The interactive parent was retained and output-integrity hashes were
  unchanged. This is cleanup evidence only; V1R2 still requires three new
  idle GPU-1 samples.

## Canonical protocol identity

- `protocol_commit = 6843fa477adc7f07acdfdb270ad7e4e3349da904`
- `command_blob_sha = 1650b873e734d8fcdf56b8bc26fff48fdb2730ac`
- `command_canonical_sha256 = 22d00fadea7eb1fb43556d4690c78113d317c6d144e96b6ad0d294d27a9369a4`
- `config_blob_sha = d3e0c104b37304278dd4074787d8781d2281a375`
- `config_canonical_sha256 = 0d15d8d6fa84049c6b4c34d6fdcaf77114f569c8d22ea9d010ae8144e6c924ea`
- `transforms_sha256 = b6a685f4b1a5b2ff3bb9b389c63a138a58119b19dd5cb6d7f671282aeecad29a`

## Attempt semantics and boundary

Preflight failures consume no attempt. The attempt count becomes one only when
the frozen `exact_training_command.sh` produces an `ns-train` process. Any
nonzero exit, OOM, NaN/Inf, checkpoint failure, disk failure, or infrastructure
failure must be recorded without retry, resume, second seed, altered output,
or GPU change. This authorization excludes SAFER, ellipsoid queries,
navigation, baseline evaluation, and G1.
