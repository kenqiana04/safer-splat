# Active Runtime V3 Paired Execution Harness R1

This task-local repair fixes two deterministic launcher bugs exposed by the first real launch while preserving the repaired runtime baseline `604981dca96cf924679aaf718b78776d858b55b1`, the PR #144 scientific protocol, and all scientific decisions.

## Verified failure mechanism

The old parent batch launched `--one TRIAL` after the result root already existed but did not provide existing-root authority. The child's global fresh-root gate rejected it before `run_one()` created `raw/trial_66`. The parent then assumed that directory existed and raised `FileNotFoundError` while writing `process_exit_code.txt`. The exact classifications are `BATCH_CHILD_ONE_MISSING_EXISTING_ROOT_AUTHORIZATION` and `PARENT_ASSUMES_CHILD_RAW_DIR_EXISTS_AFTER_EARLY_CHILD_FAILURE`.

## Narrow child authorization and parent recovery

The parent now launches `--one TRIAL --batch-child` with a one-time random token. A root-level authorization record binds the token hash, exact retry1 result root, current source HEAD, execution-lock SHA-256, branch, protocol SHA-256, repaired runtime head, and live parent PID. The flag is valid only with `--one` and without `--resume`; ordinary manual `--one`, wrong-root use, stale parent, missing token, or identity mismatch is rejected.

If a child exits before creating its raw trial directory, the parent writes stdout, stderr, exit code, GPU-release result, and typed metadata under `parent_failures/trial_<id>/`, returns a nonzero hard stop, does not retry, does not fabricate an immutable trial evidence lock, and does not increment completed trials. The normal child-created raw path is unchanged.

## Frozen boundary

- Protocol source is PR #144, byte-identical SHA-256 `2de32310c84db49f0b8982e2bb63f15d234732250a5c3ddf859fdb75386439c5`.
- Primary cohort is exactly 85 trials with the frozen order; development-exposed trials are excluded.
- Future execution is serial, separate-process, seed 0, maximum 500 cycles, official Python environment, GPU 1.
- V3 runtime authority is `r_hard=0.015 q`, `m_reserve=0`, `rho_seg=0`; historical `0.025 q` is diagnostic-only and has no runtime, routing, veto, ranking, backup, terminal, or arbitration authority.
- Reference V2 evidence is immutable and reusable for the same 85 pairs; Reference rerun is forbidden.

## Repair carried forward

The repaired runtime source is the protected baseline. The prior missing trace occurred when a typed post-L2 routing block bypassed the existing ActiveRunner/ActiveCommitTransaction no-action trace transaction. The repaired path emits a Supervisor-owned non-commit decision and uses the existing no-action trace authority. This harness does not alter that source or any method contract.

## Result-root disposition

The failed root `/disk1/zlab/v3_execution_records/active_runtime_paired_validation_v3_r1_20260914` is superseded, read-only diagnostic evidence. It is never resumed, imported, analyzed, or reused. The only authorized next root is `/disk1/zlab/v3_execution_records/active_runtime_paired_validation_v3_r1_retry1_20260915`, which must remain absent until a later manual collection task. First-launch collision protection remains universal. Explicit user resume is accepted only for this exact frozen root with a committed clean execution lock.

## Analyzer boundary

The analyzer is copied and frozen with the original hard-safety and paired-NI constants, but the launcher never calls it and the analyzer requires an explicit post-collection authorization flag. No GPU preflight, trial, Reference rerun, oracle, Official100, Formal outcome, or analyzer execution occurred in this task.

## Counts and validation boundary

The failed historical attempt performed one zero-cycle GPU preflight and zero scientific trials. This repair performs zero GPU preflights, zero Active scientific trials, zero analyzer runs, zero Reference reruns, zero Official100 runs, and zero new Formal outcomes. CPU-only regressions cover authorized and unauthorized child entry, wrong roots, early failure preservation, normal raw handling, first launch, explicit resume, analyzer exclusion, and old-root non-reuse.

`FINAL_STATUS=PASS_R1_BATCH_CHILD_ROOT_AND_EARLY_FAILURE_REPAIR`

`FINAL_DECISION=READY_FOR_MANUAL_ACTIVE_RUNTIME_V3_PAIRED_COLLECTION_R1_RETRY1`

`ONLY_NEXT_TASK=MANUALLY_START_FROZEN_ACTIVE_RUNTIME_V3_PAIRED_COLLECTION_R1_RETRY1`
