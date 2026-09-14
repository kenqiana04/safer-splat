# Active Runtime V3 trace-cardinality repair report

## Outcome

`trial_73_retry3` is the only complete post-repair GPU regression. It passed the runtime evidence contract: 434 returned public cycles, 434 trace records, 434 locked records, 434 persisted trace lines, 433 plant commits, finalized trace, and no hard blocker. The final public cycle is a typed no-action assurance boundary and is present in the trace.

The first two task-local launch attempts did not enter the runtime: retry1 stopped at the old harness branch gate and retry2 stopped before GPU because the isolated worktree lacked ignored dataset/map symlinks. Their partial directories are retained as task-local infrastructure evidence. They are not trial evidence and were not mixed into the successful retry3 result.

## Root cause and repair

The old trial-73 evidence had 355 cycle observations but only 354 trace records. Its final cycle had L1/C0/L2 PASS, then `L3_DISCOVERY_ADMISSION=WARNING`; exact-one frozen transition lookup for `L2_PASS` required `OPEN`, returned `BLOCKED_MISSING / ROUTING_RULE_MISSING`, and correctly did not enter L3. `ActiveCycleCoordinator._blocked_result` returned a boundary result directly and bypassed `ActiveRunner.commit_active_decision` and its existing `ActiveCommitTransaction` no-action trace branch.

The repair adds only a Supervisor-owned non-commit `ROUTING_BLOCK` decision and routes every returned blocked cycle through the unchanged ActiveRunner/ActiveCommitTransaction path. This appends `ASSURANCE_BOUNDARY_NO_ACTION`, performs zero plant/token side effects, and preserves the typed routing reason. No transition row, deadline interpretation, controller, certificate, map, geometry, dynamics, or scientific protocol changed.

## Post-repair integrity

The successful regression reports: `hard_runtime_radius_q=0.015`, `runtime_margin_q=0`, `rho_seg_q=0`, historical diagnostic radius `0.025 q` with runtime authority false, finalization `FINALIZED`, selected/executed mismatch `0`, nonfinite `0`, actuator violation `0`, evidence incomplete `0`, recovery required `0`, plant outcome unknown `0`, duplicate plant `0`, duplicate trace `0`, exception `0`, CUDA OOM `0`, and GPU released `true`.

The old paired result root remains read-only diagnostic evidence. The old four complete trials are not reused in a repaired primary cohort. No scientific analyzer, progress comparison, NI analysis, or 85-trial continuation was run.

## Validation

- 189 CPU behavior/V3/repair tests passed; the only excluded upstream test is the stale protected-blob identity assertion for the two runtime files this repair is explicitly authorized to modify.
- Protected scope audit passed: only `active_cycle.py` and `supervisor.py` changed under runtime; ActiveRunner, commit transaction, PlantCommit, BackupTokenStore, TerminalRuntime, TraceWriter, frozen protocol, and old harness are byte-identical.
- Existing Supervisor `bypass_decision`, `arbitrate`, and `certify_candidate` AST hashes are unchanged.
- `git diff --check` and Python compilation passed.

This is runtime evidence-contract repair only. It does not authorize scientific collection or efficacy claims.
