# Minimal code path for the G6 universal blocker

The data-only funnel was frozen before this source trace. The trace is limited to five functions/files on the formal execution and canonicalization path.

1. `reproduction/collection/l2_h1_prospective_shadow_cohort_v1/run_one_formal_trial.py` — `main` (lines 41–100)
   - Relevant condition: every formal attempt dispatches `server_run_one.py` with arm `C`, records the result-log count, and does not interpret scientific status.
   - Diagnostic interpretation: 14,122 result records prove worker output records existed; they do not prove L2 was reached.

2. `reproduction/equivalence/l2_h1_shadow_instrumentation_off_vs_on_v1/server_run_one.py` — `build_real_frozen_adapter` (lines 132–195)
   - Relevant condition: `l0` maps the current-map query to PASS/FAIL/UNKNOWN; `l1` and `l2` are separate callables injected into `ReadOnlyFrozenCertifierAdapter`.
   - Diagnostic interpretation: the formal run used the real frozen adapter. A non-PASS L0 result is possible before either L1 or L2 is called.

3. `reproduction/instrumentation/l2_h1_on_policy_shadow_instrumentation_v1/frozen_certifier_adapter.py` — `ReadOnlyFrozenCertifierAdapter.evaluate` (lines 72–110)
   - Relevant condition: after `_l0(payload)`, any L0 status other than PASS sets `l1={status: NOT_REACHED, reason: L0_BLOCKED}` and `l2={status: NOT_REACHED, reason: L0_BLOCKED, reached: false}`. `_l1` is called only in the L0-PASS branch, and `_l2` only in the L1-PASS branch.
   - Diagnostic interpretation: the observed `l1_status=NOT_REACHED` plus `l2_reachability_reason=L0_BLOCKED` is a direct signature that L0 blocked before L1/L2 evaluation. It is not an L1 FAIL/UNKNOWN result and not an L2 typing failure.

4. `reproduction/instrumentation/l2_h1_on_policy_shadow_instrumentation_v1/shadow_worker.py` — `ShadowWorker.run` (lines 49–75)
   - Relevant condition: each immutable payload is captured, passed to `adapter.evaluate`, then its returned record is appended with run/trial/step identities.
   - Diagnostic interpretation: a complete result record is emitted even when the adapter legitimately reports L1/L2 `NOT_REACHED`.

5. `reproduction/analysis/l2_h1_prospective_shadow_cohort_v1/build_formal_analysis_table.py` — canonical row builder (lines 83–118)
   - Relevant condition: G6 requires `result.l1_status == PASS`; G7 requires `l2_reached is true`; G8 requires typed PASS/FAIL/UNKNOWN. The writer copies the observed status/reason fields without remapping `NOT_REACHED` to PASS.
   - Diagnostic interpretation: all 14,122 rows fail first at G6. G7/G8 are downstream consequences rather than independent primary causes.

The compact recovery did not retain the L0 PASS/FAIL/UNKNOWN frequency breakdown, so the exact composition of L0 non-PASS statuses is not estimated here. That limitation does not affect the demonstrated branch-level cause: all rows carry the frozen `L0_BLOCKED` reachability reason and never enter L1.
