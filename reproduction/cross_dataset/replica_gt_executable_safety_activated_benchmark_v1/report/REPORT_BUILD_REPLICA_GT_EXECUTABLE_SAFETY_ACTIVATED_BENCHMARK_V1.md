# Report: Replica GT Executable-Safety Activated Benchmark V1

## Outcome

`BLOCKED_BY_METHOD_FAIRNESS_CONTRACT_MISMATCH`

`RECONCILE_REPLICA_GT_ACTIVATED_BENCHMARK_METHOD_CONTRACT`

Only next task: `FREEZE_REPLICA_GT_EXECUTABLE_SAFETY_METHOD_MATRIX_V1`.

The benchmark stopped at the preregistered Phase-0 method-fairness gate. PR #84 freezes a deterministic ordering function over caller-supplied `alternative_controls`, but it does not freeze the concrete alternative accelerations, candidate IDs, library size, or canonical library identity. Creating those inputs here would alter B3 after outcomes could be observed and violate the explicit no-library-change boundary. No candidate tuple, stage predicate, registry state, reference outcome, one-step method run, or logical-time episode was executed.

## Required closeout

1. **Branch:** `replica-gt-executable-safety-activated-benchmark-v1`.
2. **Draft PR:** created after final validation against `fas-cbf-unified-executable-safety-certifier-v1`.
3. **Commit:** `test(reproduction): benchmark activated executable-safety gates on Replica GT` after final validation.
4. **Base/head:** PR #84 head `04ebca2b1b35124ad0e61ebed96e491c9edae4bb`; result head recorded in Git/PR metadata after commit.
5. **PR #84 preserved:** `OPEN`, draft `True`, mergeable `MERGEABLE`, unmerged.
6. **Frozen certifier identity:** 15 canonical Git-blob artifacts; manifest `1f9f007d0897178552d68668f124873bf0a9f38789bc5eba36e6d84fd0f2f15d`.
7. **Map identity:** `3b318a98a454ec5c36410b3c41dfb3dd4a25b7b5a1899f1f2c939fbf24ad0e55`, all array/registry checks pass.
8. **Reference identity:** official mesh `274677d9b7caa413230363b68f4aa472e5cc1afe87e422a489fa1b7d844c6182`; validated oracle assets frozen read-only.
9. **Method matrix:** B0/B1/B2 are definable; B3 is not executable from frozen inputs.
10. **Fairness audit:** `BLOCKED_BY_METHOD_FAIRNESS_CONTRACT_MISMATCH`.
11. **Normative model:** `POSITION_FIRST_FORWARD_EULER_DOUBLE_INTEGRATOR_V1` unchanged.
12. **Actuator/robot/margin/dt:** `u,v in [-0.1,0.1]^3`, robot `0.1 m`, margin `0.01 m`, `dt=0.05 s`.
13. **Candidate generator:** guarded and not invoked.
14. **Candidate count:** 0 of a frozen maximum 300000.
15. **Physical-valid count:** 0.
16. **Stage funnel:** zero at every stage because the fairness gate precedes search.
17. **G0-G5 counts:** all zero; these are not outcome rates.
18. **Quota case:** not assigned; quota evaluation requires a valid method matrix.
19. **Registry count:** 0.
20. **Registry SHA:** not created; no invalid registry was locked.
21. **Three-process rebuild:** not run; rebuild count 0.
22. **Prelock reference reads:** 0.
23. **Selection leakage:** `PASS_NO_SELECTION_OCCURRED`; no selection or deletion occurred.
24. **One-step run count:** 0.
25. **Logical episode count:** 0.
26. **Logical step count:** 0.
27. **B0 result:** not executed; no scientific outcome.
28. **B1 result:** not executed; no scientific outcome.
29. **B2 result:** not executed; no scientific outcome.
30. **B3 result:** not executable from the frozen PR #84 inputs.
31. **G1 evidence:** unavailable; no segment-gate causal claim.
32. **G2 evidence:** unavailable; no backup-gate causal claim.
33. **G3 evidence:** unavailable; alternative rescue cannot be evaluated fairly.
34. **G0 over-rejection:** unavailable; no denominator exists.
35. **Terminal semantics:** upstream contract preserved; no terminal state evaluated.
36. **Fail-closed semantics:** no scientific fail-closed result; task blocking is not `SAFE_STOP`.
37. **Represented false-safe:** no trial; count 0 is an execution count, not an estimated rate.
38. **Reference collision:** not evaluated; oracle query count zero.
39. **Map-reference disagreement:** not evaluated; count 0.
40. **Progress:** not evaluated.
41. **Runtime:** no method decision timed; upstream PR #84 timing is not reused as benchmark timing.
42. **50 ms deadline:** not estimable; decision count and miss count are zero, with no real-time claim.
43. **Paired statistics:** no state-level pairs; no tests, effects, CIs, or p-values computed.
44. **H1-H5:** preregistered but all `NOT_TESTED_METHOD_FAIRNESS_BLOCK`.
45. **Unresolved evidence:** every causal gate, rescue, reference, progress, and deadline claim remains unresolved.
46. **Map training/mutation:** 0/0; dataset switch 0.
47. **Tuning:** controller 0; safety threshold 0.
48. **Protected-source mutation:** 0.
49. **GPU final:** `1, NVIDIA GeForce RTX 4090, 6 MiB, 0 %`; compute processes 0; task processes 0.
50. **Watchdog/SSH:** watchdog `Running`, loopback listener `True`; restart counts zero.
51. **Operational autonomy:** 3 recorded actions; task-owned cleanup 0.
52. **Validator:** `PASS_REPLICA_GT_EXECUTABLE_SAFETY_ACTIVATED_BENCHMARK_VALIDATION`; syntax 15 sources, pytest 6 passed.
53. **FINAL_STATUS:** `BLOCKED_BY_METHOD_FAIRNESS_CONTRACT_MISMATCH`.
54. **FINAL_DECISION:** `RECONCILE_REPLICA_GT_ACTIVATED_BENCHMARK_METHOD_CONTRACT`.
55. **Server report:** `/disk1/zlab/maintenance_records/replica_gt_executable_safety_activated_benchmark_v1/report/REPORT_BUILD_REPLICA_GT_EXECUTABLE_SAFETY_ACTIVATED_BENCHMARK_V1.md`.
56. **Downstream handoff:** `report/downstream_handoff.json`.
57. **Only next task:** `FREEZE_REPLICA_GT_EXECUTABLE_SAFETY_METHOD_MATRIX_V1`.

## Claim-evidence map

| Claim | Evidence | Status |
| --- | --- | --- |
| PR #84 and external assets retain the required identities | canonical Git blobs and read-only server hashes | supported |
| B0-B2 share definable primary inputs | frozen method/API audit | supported |
| B3 can be compared fairly to B2 | no concrete alternative values, IDs, size, or identity in PR #84 | blocked |
| Any gate improves safety, availability, or progress | no candidate or method execution | unsupported |

## Adversarial self-review

- **Contribution:** this result identifies a reproducibility gap in the method matrix; it is not a performance result.
- **Clarity:** the missing B3 inputs and exact resume prerequisite are explicit.
- **Experimental strength:** no experiment was run after the fairness failure, so no empirical effect is claimed.
- **Evaluation completeness:** H1-H5 remain untested and every result file is marked presearch-blocked.
- **Method soundness:** inventing an alternative library here would change the scientific method and invalidate causal attribution.
