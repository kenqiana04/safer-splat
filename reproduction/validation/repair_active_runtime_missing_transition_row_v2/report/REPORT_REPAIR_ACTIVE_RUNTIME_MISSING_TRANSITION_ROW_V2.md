# Report: Repair Active Runtime Missing Transition Row V2

## Answer first

The missing reachable tuple is closed by one new rule, `ARB_BACKUP_GUARD`: at `ARBITRATION`, a factually certified PRIMARY or ALTERNATIVE candidate plus a valid retained backup and a final-guard `WARNING` or `EXPIRED` routes to `BACKUP_EXECUTION`. It does not erase the candidate fact, does not relax backup validation, and does not create a new commit path.

The repaired trial 25 reached cycle 147 with the unique WARNING observation and executed the retained backup through the existing `BACKUP_COMMIT` path. It then continued naturally to `NATIVE_NOT_MOVING` after 334 cycles. There was no `ROUTING_RULE_MISSING`, unauthorized primary commit under WARNING, trace mismatch, identity mismatch, or integrity failure.

## Authority delta and regressions

- The transition authority changed from 43 to 44 rows. The prior 43 rows remain semantically unchanged; `ARB_NAV` remains OPEN-only and `ARB_BACKUP` remains candidate-NONE.
- Table, executable routing design, runtime count invariant, and `AuthorityRegistry.transition_table_identity` are synchronized.
- Targeted routing: 9/9 PASS.
- 44-row fidelity/dynamic resolution/exact-one: PASS.
- Active Runtime CPU suite: 179/179 PASS.
- Frozen PR #127 milestone denominator: 96/96 PASS using only the already-authorized PR #132 typed-result compatibility and mechanical ID rebinding.
- BYPASS does not execute `route_transition` or `arbitrate`; PR #131 frozen BYPASS evidence is reused and no GPU BYPASS was rerun.

## Focused trial 25

The sole scientific rerun used the frozen map identity, trial 25 start/goal, dt, CBF-QP, canonicalization, geometry, engineering deadline, and max_steps=500 on GPU 1. Cycle 147 committed one `RETAINED_BACKUP` action (`action:sha256:10abb7a5dc826c4041bd0b7aaa8a450f7e379307f5e8ce8a8c57f8006545800a`). Across the trial there were 333 primary commits, one retained-backup commit, 334 plant commits, 334 trace records, 333 token activations, and one token consumption. GPU 1 was clean afterward.

The post-hoc frozen oracle remained feedback-free: collision proxy false, certification-margin violation false, goal not reached, normalized progress 0.8528618340. The result is evaluation eligible.

## Evidence reuse and rebuilt pilot

The other nine repaired Active traces recorded zero WARNING and zero EXPIRED observations, so none entered the new rule precondition and all were reused. All ten frozen Reference arms were reused. The rebuilt pilot therefore has 10/10 eligible pairs.

Reference versus Active: collision proxy 0/10 vs 0/10; margin violation 0/10 vs 0/10; goals 0/10 vs 0/10. Mean normalized progress is 0.340029482 vs 0.340001834; median is 0.232968618 for both. Mean paired Active-minus-Reference progress is -0.0000276483 and median is 0. There is no new structural liveness blocker.

## Boundaries

No controller, QP, candidate canonicalization, geometry, map, deadline value, oracle definition, scientific parameter, Reference arm, other Active arm, official100, or GPU BYPASS execution changed. The result closes the routing/integrity blocker; it does not claim improved performance.

`FINAL_STATUS=PASS_REPAIR_ACTIVE_RUNTIME_MISSING_TRANSITION_ROW_V2`

`FINAL_DECISION=FREEZE_FORMAL_PAIRED_EXPERIMENT_PROTOCOL_V2`

Only next task: `FREEZE_FORMAL_PAIRED_EXPERIMENT_PROTOCOL_V2`.
