# Active Runtime V3 Paired Execution Harness R1

This is a pre-outcome harness re-freeze against repaired runtime commit `604981dca96cf924679aaf718b78776d858b55b1` (PR #146). It does not contain collection outcomes.

## First-launch sequencing correction

The launcher now runs CPU static preflight and the CPU validator while the fresh R1 result root is still absent. Only after both pass does it create the root and start tmux; the tmux command begins with explicitly authorized `--gpu-preflight --resume` and then `--batch --resume`. First-launch collision refusal remains active, resume remains explicit, and the analyzer is never auto-run.

## Frozen boundary

- Protocol source is PR #144, byte-identical SHA-256 `2de32310c84db49f0b8982e2bb63f15d234732250a5c3ddf859fdb75386439c5`.
- Primary cohort is exactly 85 trials with the frozen order; development-exposed trials are excluded.
- Future execution is serial, separate-process, seed 0, maximum 500 cycles, official Python environment, GPU 1.
- V3 runtime authority is `r_hard=0.015 q`, `m_reserve=0`, `rho_seg=0`; historical `0.025 q` is diagnostic-only and has no runtime, routing, veto, ranking, backup, terminal, or arbitration authority.
- Reference V2 evidence is immutable and reusable for the same 85 pairs; Reference rerun is forbidden.

## Repair carried forward

The repaired runtime source is the protected baseline. The prior missing trace occurred when a typed post-L2 routing block bypassed the existing ActiveRunner/ActiveCommitTransaction no-action trace transaction. The repaired path emits a Supervisor-owned non-commit decision and uses the existing no-action trace authority. This harness does not alter that source or any method contract.

## Fresh execution root and evidence

Future results use `/disk1/zlab/v3_execution_records/active_runtime_paired_validation_v3_r1_20260914`. First launch refuses a pre-existing root. Resume is explicit and skips only complete immutable trial evidence; partial evidence hard-stops. Every completed public cycle must have exactly one trace, including a legitimate assurance-boundary cycle, while plant commits may be lower.

## Analyzer boundary

The analyzer is copied and frozen with the original hard-safety and paired-NI constants, but the launcher never calls it and the analyzer requires an explicit post-collection authorization flag. No GPU preflight, trial, Reference rerun, oracle, Official100, Formal outcome, or analyzer execution occurred in this task.

## Validation

CPU-only validator, Python compilation, shell syntax, hash checks, protected-diff checks, map/checkpoint/reference checks, and fresh-root checks must pass before any later manual collection authorization.
