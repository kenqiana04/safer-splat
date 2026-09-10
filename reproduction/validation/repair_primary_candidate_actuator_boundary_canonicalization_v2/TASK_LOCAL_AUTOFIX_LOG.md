# Task-local autofix log

All entries below were infrastructure or harness-only fixes. None changed the runtime method, frozen inputs, Reference evidence, oracle definitions, actuator limits, C0 comparator, QP, map, or scientific thresholds.

1. The server checkout's `origin` was a local snapshot and could not fetch the new commit. The exact repair commit was transferred with a Git bundle and checked out in the task-owned source checkout.
2. The new task worktree lacked the existing `data/stonehenge` link. The frozen data path was linked before the successful P0/C0 recheck; the failed pre-query attempt produced no scientific result.
3. The first smoke launch preceded creation of the task-local harness directory. The directory and harness were installed; that empty launch produced no scientific execution.
4. The first max-200 override was placed in an oracle-only branch, so a trial-90 diagnostic attempt ran 242 cycles. It is retained under `autofix_attempts` and excluded from the formal small-smoke record.
5. A diagnostic error formatter initially referenced `typed_reason` instead of the frozen `typed_stop_or_failure_reason`. The task-local formatter was corrected; the failed formatter attempt is excluded.
6. Aggregate-only JSON output used a newline argument unavailable on the server Python path helper. The task-local writer was changed to explicit UTF-8 bytes; metric definitions and inputs were unchanged.

The trial-25 `ROUTING_RULE_MISSING` and ensuing trace-cardinality failure are not classified as autofixes. They are preserved as the genuine next method/runtime-level signal.
