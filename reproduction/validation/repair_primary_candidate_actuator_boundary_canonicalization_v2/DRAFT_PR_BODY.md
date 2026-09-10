## Summary

This Draft PR closes PR #135's `FLOAT32_ACTUATOR_BOUNDARY_CANONICALIZATION_GAP` at the `PRIMARY_NATIVE_CBF_QP` adapter boundary. It canonicalizes only values exactly equal to the promoted IEEE-754 binary32 representation of a frozen conceptual actuator bound. It does not add clipping, an epsilon, or a relaxed C0 comparison.

## Runtime change

- `PrimaryProposalAdapter` accepts explicit frozen actuator bounds and `IEEE754_BINARY32` source scalar authority.
- Exact `float32(±0.1)` representations map to conceptual `±0.1` before Candidate construction.
- All nonmatching values, including true out-of-bound values, are unchanged.
- Direct composition/test call sites pass bounds from `AuthorityRegistry`.
- C0, actuator bounds, QP, Supervisor, L1/L2/L3, terminal, deadline, map, and oracle semantics are unchanged.

## Validation

- Targeted adapter/C0: 9/9 PASS.
- Active Runtime CPU suite: 169/169 PASS.
- PR #135 cycle-0 recheck: affected 5/5 PASS; controls 5/5 PASS and unchanged.
- True `±0.100001` violations remain unchanged and fail C0.
- Small Active smoke closes the old cycle-0 failure for trials 5 and 25 and preserves trial 90 behavior.

## Repaired Pilot

Only the 10 Active arms were rerun. The 10 PR #134 Reference arms were reused by exact evidence identity; Reference rerun count is zero.

- 10/10 Active arms reached a terminal record.
- 9/10 are execution-complete and evaluation-eligible.
- 10/10 produced at least one primary commit; early terminal count is 0/10.
- Eligible Active collision proxy and margin violation: 0/9 and 0/9.
- Eligible normalized progress mean/median: 0.2830174 / 0.2157787.
- Across the 9 eligible pairs, Active-minus-Reference progress delta is 0 for every pair.
- Eligible L1/C0/L2/L3: 1,142 PASS and 0 FAIL/UNKNOWN at every layer.

Trial 25 is deliberately excluded from scientific aggregation. After 147 certified primary commits it emitted `ROUTING_RULE_MISSING`; the absent outcome trace then triggered the trace-cardinality fail-closed gate. No unverified action was executed. This is a distinct method/runtime signal and is not repaired here.

## Scope boundary

No Reference rerun, official100, ablation, parameter tuning, C0 relaxation, actuator clipping, QP redesign, or raw result tree is included.

`FINAL_STATUS=PASS_REPAIR_BUT_PILOT_REVEALS_NEXT_METHOD_LEVEL_SIGNAL`

`FINAL_DECISION=DIAGNOSE_ACTIVE_RUNTIME_ROUTING_RULE_MISSING_AFTER_PRIMARY_PROGRESSION_V2`

Only next task: `DIAGNOSE_ACTIVE_RUNTIME_ROUTING_RULE_MISSING_AFTER_PRIMARY_PROGRESSION_V2`.
