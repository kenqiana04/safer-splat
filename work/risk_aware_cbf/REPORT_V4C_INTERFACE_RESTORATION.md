# REPORT: V4-C Executable Artifact Restoration and R1 Interface Reopening

## Status Update

The earlier artifact-restoration task recovered the V4-C recovery runner,
sweep, analysis script, and official smoke wrapper from the Priority-1 4090
worktree. The follow-up dependency-closure task has now restored the two exact
helper imports that previously blocked M2:

- `run_risk_aware_v1_pre_cbf_comparison.py`, SHA256
  `e846ff625ed52d197844bdb2f56df72ab8e09cb3d94f0b42724520112268176e`
- `run_v4b_corrective_dt_filter.py`, SHA256
  `573c0587e238eb160928a8b5349239fc852af91791877d87f6abe55e0062f862`

Both came from `/disk1/zlab/projects/safer-splat` at
`master@57c55485e357343c3d166a9123ab9a9275c12067`; source and target hashes
match. They were untracked in that source worktree, so provenance is based on
the Priority-1 files plus multiple byte-identical July-era copies, not on a
claim of Git-tracked helper contents.

## Closure Validation

AST analysis found no missing transitive local Python dependency after the two
helpers were restored. All 25 referenced helper symbols exist. The helpers,
V4-C runner, and official wrapper compile/import in the original 4090
environment, and all expected `--help` paths succeed without running a trial.

Direct imports initialize CUDA and change Python RNG state but do not launch an
experiment or write repository files. A thin shadow adapter restores RNG state,
clones evaluation tensors, calls only the original V4-C functions, and never
executes the selected control.

## Interface Decision

A deterministic real-flight interface check matched all 22 direct-versus-
adapter fields with zero critical mismatch. M0, M1, and M2 are therefore
`shadow_evaluable`; M3 remains `interface_only` and excluded.

`restoration_decision = dependency_closure_restored_r1_stage0_ready`

No five-context audit, active supervisor, recovery performance validation,
retuning, benchmark trial, or core-source change was performed.

The current task restores the original V4-C dependency closure and reassesses interface readiness; it does not revalidate recovery performance or R1 effectiveness.

The restored dependency closure makes the preregistered R1 shadow audit executable in a separate task; no shadow or active effectiveness has yet been established.
