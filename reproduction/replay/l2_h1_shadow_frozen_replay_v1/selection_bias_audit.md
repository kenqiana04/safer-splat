# Selection-bias audit

Status: **PASS_WITH_EXPLICIT_SOURCE_AND_MISSINGNESS_BIAS**

The source universe was frozen before L2 results. Formal replay coverage is 2594/6853 (37.852036%). All 4259 NOT_REPLAYABLE rows are historical rollout-step rows lacking a numeric `u_k`; 792 of them also lack candidate identity. They were not converted to L2 UNKNOWN.

Primary evaluation is limited to 788 rows with stored historical L1 PASS. It is source-heterogeneous: Replica contributes 710 evaluated rows, Flight 78, and Stonehenge 0. Executed/selected and logged non-executed candidate strata are reported separately. These structural missingness and reachability filters limit prevalence generalization beyond the frozen cohort. No row was selected after observing an L2 result, no easy row was deleted, and no risk row or candidate was synthesized.
