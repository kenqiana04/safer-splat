# Diagnose Active Runtime routing-rule-missing after primary progression V2

## Answer first

**Exact failure.** The unique failure is trial 25, cycle 147, lookup 6: `source_phase=ARBITRATION`, `event=ARBITRATE`, `deadline=WARNING` at `FINAL_COMMIT_GUARD`, a certified `PRIMARY` candidate is available, and a retained backup token is present and valid. The executable lookup returns zero matches across all 43 frozen rules and fail-closes as `ROUTING_RULE_MISSING`.

**Exact discriminant.** Cycle 146 reaches the same arbitration shape—certified primary plus valid retained backup—and resolves `ARB_NAV` under `deadline=OPEN`. At cycle 147 the categorical routing change is `OPEN → WARNING`. `ARB_NAV` is excluded by its OPEN-only deadline requirement and guard; `ARB_BACKUP` accepts the valid backup and any deadline but is excluded by its `candidate=NONE` requirement and no-certified-candidate guard.

**Root cause.** `R1 MISSING_LEGITIMATE_TRANSITION_ROW`. The frozen transition authority lacks a row for a factually certified navigation candidate that is no longer final-commit admissible because the deadline is non-OPEN while a valid retained backup already exists. The context and token are internally consistent; neither should be falsified to fit an existing row.

**One-sentence diagnosis.** The post-primary failure is best explained by a missing deadline-aware arbitration transition for `certified candidate + valid backup + WARNING`; no runtime source or scientific result is changed.

## Frozen causal window

The cycle-147 L3 lookup succeeds first: `L3_WITNESS_FOUND → L3_FOUND → ARBITRATION`, with the L3 admission deadline still OPEN. The final commit guard is observed later, after elapsed time reaches 0.7651723456 s, producing WARNING with 0.0348276544 s remaining. This later observation is valid input to Supervisor routing; it is not evidence that the earlier certificate disappeared.

The previous 147 primary commits remain preserved. Trial 25 remains evaluation-ineligible exactly as PR #136 recorded; this diagnosis neither imputes its scientific metrics nor changes the 9-pair eligible analysis.

## Mechanical 43-rule elimination

`ROUTING_MATCH_ELIMINATION.csv` records every predicate outcome. No row passes all predicates. Only the arbitration rows match phase and event. The two nearest rows are:

- `ARB_NAV`: candidate and backup predicates match; deadline and guard reject WARNING.
- `ARB_BACKUP`: deadline and backup predicates match; candidate requirement and guard reject the still-present certified primary.

There is no lookup implementation ambiguity and no first-match artifact: the exact-one resolver correctly reports zero matches for a tuple not represented by the frozen table.

## Backup-token diagnosis

The retained token is `ACTIVE`, validation is `PASS`, its expected state and time equal cycle 147, authority identity matches, cursor 0 exposes a current action, and no invalidation reason exists. It is therefore relevant fallback evidence, not the cause of the missing route. Clearing `certified_candidate_available` merely to make `ARB_BACKUP` match would erase a true certificate fact and encode deadline policy outside Supervisor.

## Passive replay boundary

Existing compact PR #136 evidence did not contain the complete lookup tuple, so exactly one authorized trial-25 passive replay was run against PR #136 head `bf6b81870e72594b78f7939f55140597710d60b1`, frozen inputs, max 500 steps, GPU 1, and no oracle. A read-only wrapper logged route inputs, per-rule predicate elimination, and the original return; it did not modify routing inputs or outputs. The replay reproduced one and only one missing lookup after 147 primary commits. GPU 1 was clean afterward.

The first launch stopped before map loading because the fresh checkout lacked the frozen `outputs` link. No scientific cycle ran. Restoring that path and retrying the same authorized replay was an infrastructure-only correction. No Reference trial, other Active trial, official100, 96-scenario suite, or full smoke was run.

## Repair boundary

The minimal next task is `REPAIR_ACTIVE_RUNTIME_MISSING_TRANSITION_ROW_V2`. It must separately freeze the missing Supervisor-owned arbitration transition and its deadline scope. It must not change context truthfulness, token mechanics, coordinator authority, certificates, controller, map, or PR #136 evidence. This task does not implement that repair.

## Final decision

- `FINAL_STATUS=PASS_DIAGNOSE_ACTIVE_RUNTIME_ROUTING_RULE_MISSING_AFTER_PRIMARY_PROGRESSION_V2`
- `ROOT_CAUSE=R1 MISSING_LEGITIMATE_TRANSITION_ROW — no frozen arbitration row covers certified primary plus valid backup at WARNING`
- `FINAL_DECISION=REPAIR_ACTIVE_RUNTIME_MISSING_TRANSITION_ROW_V2`
- Remaining blockers: the missing row remains unimplemented; Active runtime pilot continuation is not authorized.
- Only next task: `REPAIR_ACTIVE_RUNTIME_MISSING_TRANSITION_ROW_V2`
