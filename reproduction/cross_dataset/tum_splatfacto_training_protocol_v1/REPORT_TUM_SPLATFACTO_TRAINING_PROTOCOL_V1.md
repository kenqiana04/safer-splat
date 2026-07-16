# REPORT: TUM Splatfacto Training Protocol V1

## Executive Summary

This no-execution protocol depends on PR #22 at `8199c9c4c5ce76e65f389e963376a8a02d784247` and freezes one standard `splatfacto` TUM_FR1_ROOM run: seed `20260716`, 240/60 split, 30,000 iterations, and final-checkpoint-only selection.
The frozen `transforms.json` SHA-256 is `b6a685f4b1a5b2ff3bb9b389c63a138a58119b19dd5cb6d7f671282aeecad29a`.

## Evidence and Frozen Contract

Stonehenge primary reference: `/disk1/zlab/projects/safer-splat/outputs/stonehenge/splatfacto/2024-09-11_100724/config.yml` (`cd6ea45ad01553f0ce1531ad08cfaf8359e95041b39c77291d94e75f2d2f2f8e`). Flight secondary reference: `/disk1/zlab/projects/safer-splat/outputs/flight/splatfacto/2024-09-12_172434/config.yml` (`7e83fb0711a1decc55518e66e43a34395188c2e2a2de0e5ec24d6bb510fb7b8d`). Model, optimizer, and budget match; legacy parser differences are overridden solely by the metric TUM contract.
Nerfstudio 1.1.5 uses `nerfstudio-data`; depth scale is exactly `0.0002` and standard Splatfacto depth objective is frozen false. The viewer is disabled with `--vis tensorboard`.
The NOT EXECUTED command is `exact_training_command.sh`; expected output is `/disk1/zlab/formal_splatfacto_runs/tum_fr1_room_splatfacto_v1/splatfacto/20260716_000000`, verified absent, non-overlapping with source data, no overwrite, and no resume.

## Boundary and Handoff

No training, run directory, checkpoint, render metric, SAFER action, or G1 action occurred. Acceptance and retry gates are preregistered only. `training_iterations_executed=0`, `checkpoint_created=false`, `safer_executed=false`, and `G1_allowed=false`.
Protocol readiness is not checkpoint or SAFER readiness. The next task requires new user authorization and may execute only this frozen command; G1 baseline remains forbidden.

## Conda Activation Strict-Mode Correction

PR #27 remains an immutable V1R3 attempt-0 blocked record: tmux briefly
started but `ns-train` never appeared. Its exact frozen script enabled nounset
before Conda activation, and `deactivate-gfortran_linux-64.sh` read an unset
`GFORTRAN` variable. This correction does not use a variable patch or alter
Conda; it keeps `set -e` and `pipefail`, activates `safer_splat_official`, and
then immediately enables `set -u`.

The old failure class was reproduced in an isolated server base-environment
probe through `deactivate-gcc_linux-64.sh` and an unset
`_CONDA_PYTHON_SYSCONFIGDATA_NAME_USED`. The corrected activation-only probe
passed with Python 3.10.20 and the expected `ns-train` path; no training,
output directory, checkpoint, evaluation, render, SAFER, or G1 work occurred.
The old/new training token lists are identical (71 tokens, zero argument
differences), and `frozen_training_config.json` is byte-identical.

Previous/new command blob identities are
`1650b873e734d8fcdf56b8bc26fff48fdb2730ac` /
`22d00fadea7eb1fb43556d4690c78113d317c6d144e96b6ad0d294d27a9369a4`
and `0d56e187039d5da75f2a147ff1c207bf9ff58efa` /
`4a39766b324ffc6c7766a3389589d748bc00925f109ec44fc72e5a705358ec94`.
The server `git fetch` for the new protocol commit timed out before the
required detached checkout could be made, so the protocol remains blocked by
server-checkout verification and does not authorize training. PR #24–#27
remain Draft evidence. A future V1R4 needs new explicit authorization, a new
branch and Draft PR, pre-created execution records before GPU sampling, and
the same activate-before-nounset policy. G1 remains forbidden.

## Cross-Platform Hash Canonicalization Correction

PR #24 correctly blocked before training because its preflight compared old
Windows CRLF hashes with Linux LF checkout hashes. Its formal attempt count is
still zero and it remains immutable blocked evidence. The command's old Windows
CRLF SHA-256 was `25e490904204622b0c2014ea4093f52efc507fb0543b675f9fe25871fd0d5b81`;
its canonical Git-blob/LF SHA-256 is
`22d00fadea7eb1fb43556d4690c78113d317c6d144e96b6ad0d294d27a9369a4`.
The configuration has the same confirmed EOL-only classification: its old
Windows CRLF SHA-256 was
`52fa5cdb93bcef333fc6e9f1c94043745a535e99d620e1f0fff85850f73f8105` and its
canonical Git-blob/LF SHA-256 is
`0d15d8d6fa84049c6b4c34d6fdcaf77114f569c8d22ea9d010ae8144e6c924ea`.

The canonical policy is SHA-256 of exact Git blob bytes at a recorded commit;
working-tree, JSON-reserialized, and PowerShell text-pipeline hashes are not
authoritative. A protocol-directory `.gitattributes` file contracts text to LF.
The command semantics and configuration JSON semantics are unchanged. An
isolated server worktree at `39d91df9b6527f8683064db524cfe7bdc6aa17e6`
verified both checkout hashes equal their canonical blobs, with no CRLF bytes,
and found the output path and checkpoints absent. GPU busy is recorded only and
does not block this correction, but GPU 1 must be checked again before any
separate future execution. A future execution requires a new branch and Draft
PR and cannot reuse PR #24. G1 remains forbidden.

Validator status: `PASS_READY_FOR_FORMAL_TRAINING_EXECUTION_AFTER_HASH_CANONICALIZATION`.
