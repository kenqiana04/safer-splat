# Multi-Candidate Canonical L2 Evidence Collision Diagnosis

## Frozen symptom

Retry1 is read-only at `/disk1/zlab/v3_repair_records/bounded_local_recovery_smoke_v1_retry1_20260918`. Its formal status remains `INCONCLUSIVE_RECOVERY_SEARCH_EXERCISED_BUT_NO_RECOVERY_COMMIT`; this diagnosis does not reinterpret it as a method failure.

The three natural witnesses are trial/cycle `15/202`, `45/168`, and `75/281`. Each has primary L1/C0/L2 PASS, primary L3 recovery eligibility, terminal pre-certificate PASS, OPEN recovery admission, rank-0 `+x` recovery C0 PASS, then `STAGE_EXCEPTION:L2:RuntimeError`. The recovery attempt records L2/L3 as `NOT_REACHED`, routes through `L2_UNKNOWN_GLOBAL`, and fail-closes to `ARB_TERMINAL` / `CERTIFIED_TERMINAL`. All scans generated the six frozen F1 candidates in order with no skipped duplicates.

## H1 confirmation

`pre_repair_reproduce_h1.py` uses the unmodified upstream `CanonicalIdentityLedger` and `CanonicalL2Runtime` on CPU. It evaluates a primary and a different recovery/alternative candidate at the same trial, cycle, snapshot, map, and geometry. The primary evaluation passes. The second evaluation raises exactly:

`RuntimeError: CANONICAL_EVIDENCE_REWRITE_FORBIDDEN:canonical_l2_x_k1_identity`

This confirms that `CanonicalL2Runtime.evaluate()` writes candidate-dependent data into one cycle-flat `canonical_l2_*` namespace. It is not a failure of the guard: the guard correctly detects a different value. The cardinality of the storage contract is wrong for more than one candidate evaluation in a public cycle.

Root cause: `MULTI_CANDIDATE_CANONICAL_L2_EVIDENCE_NAMESPACE_DEFECT`.

## Classification boundary

This is an evidence/instrumentation cardinality defect. It does not change or contradict the frozen CBF computation, `0.015 q` geometry, F1 generator, trigger, Supervisor routing priority, actuator authority, canonical transition arithmetic, or fail-close terminal behavior. The existing evidence proves the generator, trigger, C0, and fallback ran as frozen; it does not prove what the real Stonehenge L2/L3 verdict would be after repair. No GPU query or trial is part of this task.

Scientific verdict remains `FAIL_POST_REPAIR_V3_PROGRESS_NONINFERIORITY_GATE`.
