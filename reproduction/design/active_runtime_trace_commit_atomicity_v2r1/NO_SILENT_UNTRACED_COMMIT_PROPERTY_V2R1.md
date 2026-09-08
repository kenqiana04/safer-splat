# No-silent-untraced-commit property V2R1

For every plant attempt, the runtime must retain a typed transaction result. If the plant confirms commitment, that result retains the `CommitReceipt`, selected and executed action identities, exact executed vector, and post-state identity even when token application, trace append, or finalization fails. A trace failure cannot erase execution, turn it into `committed=false`, or imply physical rollback.

`COMMITTED_TOKEN_INCOMPLETE` and `COMMITTED_TRACE_INCOMPLETE` are execution facts with incomplete evidence. Both force a non-runnable session and require reconciliation; neither is a safe stop. `PLANT_OUTCOME_UNRESOLVED` is distinct from both committed and not committed, forbids automatic retry, and requires manual or separately authorized reconciliation.

The selected software transaction state machine is memory-only. It does not claim physical ACID, crash durability, restart recovery, filesystem durability, or rollback authority.
