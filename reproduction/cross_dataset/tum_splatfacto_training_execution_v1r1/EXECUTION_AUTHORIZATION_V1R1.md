# Execution Authorization: Formal TUM Splatfacto Training Execution V1R1

The user explicitly and separately authorized **Formal TUM Splatfacto Training
Execution V1R1**. Exactly one frozen command, seed `20260716`, and formal start
are permitted only after all preflight checks pass.

## Previous blocked execution

- `previous_execution_pr = 24`
- `previous_execution_status = BLOCKED_BY_PROTOCOL_HASH_MISMATCH`
- `previous_attempt_count = 0`
- `previous_branch_reusable = false`

## Canonical protocol identity

- `protocol_commit = 6843fa477adc7f07acdfdb270ad7e4e3349da904`
- `command_blob_sha = 1650b873e734d8fcdf56b8bc26fff48fdb2730ac`
- `command_canonical_sha256 = 22d00fadea7eb1fb43556d4690c78113d317c6d144e96b6ad0d294d27a9369a4`
- `config_blob_sha = d3e0c104b37304278dd4074787d8781d2281a375`
- `config_canonical_sha256 = 0d15d8d6fa84049c6b4c34d6fdcaf77114f569c8d22ea9d010ae8144e6c924ea`
- `transforms_sha256 = b6a685f4b1a5b2ff3bb9b389c63a138a58119b19dd5cb6d7f671282aeecad29a`

## Attempt semantics and boundary

Preflight failures consume no attempt. Attempt count becomes one only after the
frozen `exact_training_command.sh` has started an `ns-train` process. A nonzero
exit, OOM, NaN/Inf, checkpoint failure, disk failure, or infrastructure failure
must be recorded without retry or resume. This authorization does not permit
SAFER, ellipsoid queries, navigation, baseline evaluation, or G1.
