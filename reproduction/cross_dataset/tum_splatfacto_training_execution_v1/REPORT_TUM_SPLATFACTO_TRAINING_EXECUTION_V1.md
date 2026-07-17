# REPORT: Formal TUM Splatfacto Training Execution V1

## Executive Summary

Formal training was **not started**. The preflight result is
`BLOCKED_BY_PROTOCOL_HASH_MISMATCH`; therefore the one authorized training
attempt remains unused. The physical 4090 GPU 1 also had an unrelated Python
compute process using 1728 MiB, recorded as `BLOCKED_BY_GPU_BUSY`.

## Authorization and Frozen Contract

- Dependency protocol commit: `b56f5eb9af1c67791466f37e1f6c2514958cdcd3`
- Execution authorization commit: `fe00d8849a666cf6e1619f8ec11251cb682124f5`
- Execution Draft PR: #24, base `tum-splatfacto-training-protocol-v1`, head
  `tum-splatfacto-training-execution-v1`, kept Draft.
- Result evidence commit: created after this server-side evidence bundle is
  pulled into the Windows Git worktree; its immutable SHA is recorded in the
  Draft PR and final task response.
- Authoritative host: `zlab-Super-Server`, conda environment
  `safer_splat_official`, CUDA-visible physical GPU 1 (`GPU-78ef17e4-66cc-4a58-fe43-67d31be8981d`).
- Expected run: `/disk1/zlab/formal_splatfacto_runs/tum_fr1_room_splatfacto_v1/splatfacto/20260716_000000`
- Attempt count: `0`; no tmux training session was started.
- Expected command SHA-256: `25e490904204622b0c2014ea4093f52efc507fb0543b675f9fe25871fd0d5b81`
- Observed command SHA-256: `22d00fadea7eb1fb43556d4690c78113d317c6d144e96b6ad0d294d27a9369a4`
- Expected frozen-config SHA-256: `52fa5cdb93bcef333fc6e9f1c94043745a535e99d620e1f0fff85850f73f8105`
- Observed frozen-config SHA-256: `0d15d8d6fa84049c6b4c34d6fdcaf77114f569c8d22ea9d010ae8144e6c924ea`
- Transforms SHA-256: `b6a685f4b1a5b2ff3bb9b389c63a138a58119b19dd5cb6d7f671282aeecad29a` (matches contract).

## Preflight Evidence

- Environment and dataparser-only preflight: passed (`TUM_FR1_ROOM`, 300 total,
  240 train, 60 val, zero frame drop, native 3x4 identity transform, parser
  scale 1, depth scale 0.0002).
- Disk and output preflight: passed (run path absent; 509.49 GiB free).
- Shell syntax: passed for all three frozen/invocation/post-training scripts.
- Protocol identity: blocked because both command and frozen-config byte hashes
  differ from the authorization contract. No frozen protocol file was changed.
- GPU: blocked because GPU 1 had an unrelated Python process. It was not killed,
  moved, or otherwise modified.
- Source asset postcheck: `True`; raw index/pose manifests and processed
  transforms retain their expected SHA-256 values.

## Non-Execution Boundary

No `ns-train`, checkpoint creation, output-directory creation, resume, retry,
tuning, second seed, `ns-eval`, rendering, SAFER loader, ellipsoid query,
navigation, baseline, or G1 operation was executed. There is no checkpoint,
metric, render, or geometry result to report.

## Validation and Next Step

Validator status: `BLOCKED_BY_PROTOCOL_HASH_MISMATCH`. This is not a training
failure and no retry is authorized. The frozen protocol hashes must first be
reconciled through a separately authorized correction; GPU availability must
also be rechecked before any future formal attempt. This task does not produce a
checkpoint candidate and does not authorize G0 or G1 execution.

## Server Evidence Paths

- The detached worktree
  `/disk1/zlab/formal_execution_worktrees/tum_splatfacto_training_execution_v1`
  was removed only after its compact evidence was copied to the Windows Git
  worktree and committed. It contains no retained source, checkpoint, log, or
  render evidence.
- No execution-record root was created because the wrapper never started.
- Formal output path retained absent:
  `/disk1/zlab/formal_splatfacto_runs/tum_fr1_room_splatfacto_v1/splatfacto/20260716_000000`.
- The retained compact evidence is the Git directory containing this report.
