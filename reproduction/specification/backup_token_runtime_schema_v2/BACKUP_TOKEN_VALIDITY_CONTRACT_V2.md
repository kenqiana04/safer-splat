# Backup Token Validity Contract V2

`BACKUP_TOKEN_STILL_VALID(x_j, context_j, token)` returns PASS only when all 19 requirements in `BACKUP_TOKEN_VALIDITY_PREDICATE_V2.json` hold simultaneously. It is an exact identity predicate under `POSITION_FIRST_FORWARD_EULER_DOUBLE_INTEGRATOR_V1`, the immutable represented map, and the frozen no-error theorem.

There is no state, action, time, tracking, or authority tolerance. IEEE-754 exact serialization establishes identity; it does not assert physical equivalence. Missing tracking error, delay, disturbance, or hardware evidence cannot be silently converted to validity.

Any map, geometry, actuator, dynamics/timebase, state, cycle, cursor, action, bundle, terminal-reference, or provenance mismatch invalidates the ACTIVE token before execution. INVALID is absorbing for that token identity. Re-entry to VALID requires a new L3 witness, new bundle, and new token identity. A future robust contract requires a separate `FREEZE_ROBUST_BACKUP_TOKEN_VALIDITY_V3` task.
