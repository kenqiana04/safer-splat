## Summary

Closes PR #137's exact `R1 MISSING_LEGITIMATE_TRANSITION_ROW` by adding one deadline-aware arbitration row, `ARB_BACKUP_GUARD`, and synchronizing the 44-row authority chain. The new row preserves the certified-candidate fact and routes a final-guard WARNING/EXPIRED context with a valid retained backup to the existing backup execution and commit path.

## Validation

- Targeted routing: 9/9 PASS
- Transition fidelity and dynamic resolution: 44/44 PASS; exact-one PASS
- Prior 43 rows semantically unchanged
- Active Runtime CPU suite: 179/179 PASS
- Frozen PR #127 milestone: 96/96 PASS
- BYPASS dependency proof: PR #131 evidence reusable; no GPU rerun
- Focused repaired Active trial 25: 334 cycles, 333 primary commits, 1 retained-backup commit, 334 trace records, exit 0, evaluation eligible
- Cycle 147: WARNING -> `ARB_BACKUP_GUARD` -> `BACKUP_EXECUTION` -> existing `BACKUP_COMMIT`
- GPU 1 clean after completion

The other nine repaired Active traces had no WARNING/EXPIRED observations and are dependency-unaffected. All ten Reference arms are reused. The rebuilt descriptive pilot has 10/10 eligible pairs, no collision-proxy or margin-violation trials, and no new structural liveness blocker.

## Scope

No controller, QP, candidate canonicalization, geometry, map, deadline value, oracle, scientific parameter, Reference arm, other Active arm, official100, or GPU BYPASS change/rerun. A pre-data missing symlink retry is preserved in the task-local autofix record.

`FINAL_STATUS=PASS_REPAIR_ACTIVE_RUNTIME_MISSING_TRANSITION_ROW_V2`

`FINAL_DECISION=FREEZE_FORMAL_PAIRED_EXPERIMENT_PROTOCOL_V2`

Only next task: `FREEZE_FORMAL_PAIRED_EXPERIMENT_PROTOCOL_V2`.
