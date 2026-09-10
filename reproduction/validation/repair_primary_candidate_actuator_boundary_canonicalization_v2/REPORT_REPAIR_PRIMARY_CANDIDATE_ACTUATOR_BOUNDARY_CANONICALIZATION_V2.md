# Repair Primary Candidate Actuator-Boundary Canonicalization V2

## Answer-first result

The narrow repair passed: all five PR #135 cycle-0 C0 failures disappeared without changing C0, the actuator bounds, or the QP. The repaired Pilot then exposed a different signal in trial 25: after 147 certified primary commits, `ROUTING_RULE_MISSING` produced a no-transaction boundary result and the harness correctly failed closed on trace cardinality. Consequently, the canonicalization repair is frozen, but only 9/10 repaired Active arms are evaluation-eligible and the next task is a focused routing diagnosis.

1. **Did the original five cycle-0 C0 failures disappear?** Yes. Trials 5, 25, 45, 75, and 85 all produced P0 PASS and C0 PASS; seven exact binary32 boundary components were mapped to the conceptual bounds.
2. **Does any C0 FAIL remain?** No C0 FAIL appears in the 10 cycle-0 rechecks or in the 1,142 eligible Pilot certificate records. Trial 25's incomplete summary cannot provide full stage counters, but its blocker is `ROUTING_RULE_MISSING`, not `F_ACTUATOR_ADMISSIBILITY_LOCAL`.
3. **What happened to the five old zero-progress trials?** Eligible normalized progress is trial 5: 0.2922964; trial 45: 0.0668499; trial 75: 0.6139030; trial 85: 0.2157787. Trial 25 is not estimable because its execution did not finalize for oracle evaluation.
4. **How many Active trials now have a primary commit?** 10/10, up from 5/10. Trial 25 has 147 preserved partial primary commits but is excluded from scientific aggregation.
5. **How many early terminal trials remain?** 0/10, down from 5/10. No terminal action was committed.
6. **Are collision proxy and margin violation still zero?** They are 0/9 and 0/9 among evaluation-eligible repaired Active trials. A 0/10 claim would be invalid because trial 25 has no eligible oracle result.
7. **What are repaired progress mean and median?** Mean 0.2830174 and median 0.2157787 over 9 eligible trials. The old all-10 Active values were 0.1358328 and 0.0011647, but the denominators differ. In the 9 eligible matched pairs, Active-minus-Reference progress delta is exactly 0.0 for every pair.
8. **What is the remaining paired progress gap?** Zero over the 9 eligible pairs. The tenth pair is not estimable, not imputed.
9. **Did primary reachability and early-terminal behavior improve?** The exact boundary artifact no longer blocks cycle 0: primary-commit reachability is 10/10 and early-terminal count is 0/10. This is repair evidence, not a formal performance claim.
10. **Was a new method-level blocker exposed?** Yes. Trial 25 reaches 147 certified primary commits, then produces `ROUTING_RULE_MISSING`; because no trace transaction is created for the boundary result, the trace-cardinality gate stops the arm. This warrants a narrow routing diagnosis, not parameter tuning.

## Exact implementation

`PrimaryProposalAdapter` now receives the frozen conceptual actuator bounds and the explicit source contract `IEEE754_BINARY32`. For each component only, it computes the exact promoted binary32 representation of each conceptual bound. Equality to that exact representation maps back to the conceptual bound; all other values are returned unchanged. The implementation uses standard-library binary packing, not NumPy, clipping, an epsilon, or a ULP admission tolerance.

The following remain unchanged from PR #135:

- `C0Admission` and its strict inclusive conceptual-bound test;
- `AuthorityRegistry` actuator bounds `[-0.1, 0.1]^3`;
- the source CBF-QP and its box constraints;
- Supervisor, L1/L2/L3, terminal, deadline, geometry, map, and oracle semantics.

True violations `-0.100001` and `+0.100001` remain unchanged and fail C0 with `F_ACTUATOR_ADMISSIBILITY_LOCAL`. Interior and near-bound nonmatching values remain unchanged.

## Validation evidence

- Targeted adapter/C0 tests: 9/9 PASS.
- Full Active Runtime CPU suite: 169/169 PASS.
- Cycle-0 P0/C0 recheck: affected 5/5 PASS; controls 5/5 PASS and unchanged; plant/oracle/episode calls all zero.
- Small Active smoke, max 200: trials 5 and 90 complete without regression; trial 25 closes the old cycle-0 C0 failure and advances for 147 commits before the new routing/trace blocker.
- Pilot: 10/10 repaired Active arms terminal; 9/10 execution-complete and evaluation-eligible; all 10 frozen PR #134 Reference arms reused without rerun.
- Eligible certificates: L1/C0/L2/L3 each 1,142 PASS, 0 FAIL, 0 UNKNOWN.
- Eligible action roles: 1,142 primary commits; 0 alternative, backup, terminal, or traced boundary actions. Trial 25 additionally preserves 147 partial primary commits and one untraced boundary attempt.
- Eligible compute summary: median across per-trial medians 0.2654777 s; median across per-trial p95 values 0.3139958 s.
- GPU 1 was clean after execution. Official100, Reference reruns, ablation, and parameter tuning counts are zero.

## Evidence boundary

This task establishes only that exact binary32 source-bound representations are canonicalized at the adapter boundary and that the PR #135 failure mechanism is closed. The 9 eligible repaired Active traces match their frozen Reference traces on progress, but the missing tenth eligible pair prevents a complete 10-pair performance conclusion. No collision-reduction, superiority, deployment, or formal-experiment claim is made.

## Decision

`FINAL_STATUS=PASS_REPAIR_BUT_PILOT_REVEALS_NEXT_METHOD_LEVEL_SIGNAL`

`FINAL_DECISION=DIAGNOSE_ACTIVE_RUNTIME_ROUTING_RULE_MISSING_AFTER_PRIMARY_PROGRESSION_V2`

Only next task: `DIAGNOSE_ACTIVE_RUNTIME_ROUTING_RULE_MISSING_AFTER_PRIMARY_PROGRESSION_V2`.
