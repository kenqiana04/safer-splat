# Atomic Backup Handoff Contract V2

Let `B_old` be the current ACTIVE token and `B_new_prepared` a complete bundle bound to candidate `u_k`. Before commit, `B_old` remains unchanged and selectable if VALID; `B_new_prepared` is not executable.

Successful navigation handoff requires exact selected candidate identity, fresh C0/L1/L2/L3 evidence, a COMPLETE prepared bundle, Supervisor commit permission, matching geometry/map/actuator/dynamics/timebase/source authorities, and no value-changing transform. One atomic transition commits `u_k`, activates `B_new` for cycle `k+1`, and marks `B_old` `RETIRED_SUPERSEDED`. There is no observable `NONE` gap.

If selection changes, commit fails, identity changes, or commit aborts, the new prepared token becomes `ABORTED_PREPARED` and `B_old` remains unchanged. Multiple complete prepared bundles may exist as evidence, but at most one token is ACTIVE and only the final selected candidate's bundle may activate.
