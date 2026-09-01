# Report: Collect L2/H1 Prospective Shadow Cohort V1

## Outcome-blind closeout

1. **PR #100 exact identity?** Yes. Open Draft, head `84cf0734bafd52ddc7b100686fb0d1f509f1e356`, branch `freeze-l2-h1-prospective-shadow-cohort-protocol-v1`.
2. **Protocol SHA exact?** Yes: `e8ea8f3fda15ab81664829ea6f71fcb37f772ad613c13f61007856c16117791a`.
3. **Execution lock SHA?** `5e20a3f0504205e8d65b91033638c5af0909ed741212a04539dcfb37eda08fe2`; all nine locked critical script hashes remained unchanged after first data.
4. **Official100 100/100?** Yes. All 100 official trials reached terminal outcome-blind QC PASS.
5. **Stable order?** Yes, exactly `0..99`; all attempts were `attempt-0`.
6. **Formal run namespace?** `formal-v1-trial-NNN-attempt-0`, disjoint from QA namespaces.
7. **Environment/map identities?** Environment SHA `807eb4b5ca1eb0adf89a405c605a552fc646af278b61ae7218d0e94bd0513273`; map authority `65c2e4a5ccfd71a0fa8d633c207397215dd8206d5f8fb77a731c05bcb0109af3`. Python 3.10.20, Torch 2.1.2+cu118, CUDA 11.8, physical GPU 1.
8. **Total intended steps?** 14,122.
9. **Total captures?** 14,122.
10. **Total result records existing?** 14,122.
11. **Total joinable records?** 14,122.
12. **Six logging-completeness rates?** Capture, selected-u, map-authority, reachability, shadow-result completion, and join completeness are each `1.0`.
13. **Strict QC errors all zero?** Yes; aggregate error count is `0`.
14. **Pre-data retry count?** `0`.
15. **Post-data deviation count?** `0`.
16. **Raw artifact manifest SHA?** `d474496716c97f9f8d1596d9cca40983796d06d537b00a8cb4739546d85b8d19`.
17. **Result artifact commitment SHA?** File SHA `3beb36d3e409483fa38b9a112e6070098309734045c3d7aae560e54ccd7b3ca2`; ordered-result commitment `1f5061412b266a9e58ba35f868734cb5b8478b02cf11b1af0c794be5850e3bff`.
18. **Raw logs committed to Git?** `0`.
19. **Intervention/replacement counts?** `0/0`.
20. **Scientific analysis performed?** No.
21. **Outcome distribution exposed?** No.
22. **FORMAL_COLLECTION_LOCK SHA?** `c30adc48099e8d7b90c980d84389cc1fa693cc1f87d3fc519089efb7cb81b756`.
23. **Validator?** `PASS_L2_H1_PROSPECTIVE_SHADOW_COHORT_COLLECTION_V1_VALIDATION` (23/23 checks).
24. **FINAL_STATUS?** `PASS_L2_H1_PROSPECTIVE_SHADOW_COHORT_COLLECTION_V1`.
25. **FINAL_DECISION?** `FREEZE_FORMAL_COLLECTION_AND_AUTHORIZE_SCIENTIFIC_ANALYSIS`.
26. **Only next task?** `ANALYZE_L2_H1_PROSPECTIVE_SHADOW_COHORT_V1`.

## Execution note

Before data collection, the server checkout deterministically materialized the PR #100 Official100 manifest to its frozen CRLF byte identity because Git checkout on Linux had produced LF bytes. The resulting byte SHA matched the frozen contract. No semantic field, protocol ordering, controller, instrumentation, map, candidate, threshold, or trial was modified.

The post-collection validator initially referenced `arm_activation.json` one directory too deep. That task-local validator path was corrected and rerun; collection scripts, locks, and raw data were untouched.

## Evidence boundary

This report certifies collection identity, completeness, integrity, and outcome blindness only. It deliberately does not reveal or summarize scientific L2 outcomes and makes no claim about collision reduction, progress, control efficacy, statistical significance, real-time capability, or deployment readiness.
