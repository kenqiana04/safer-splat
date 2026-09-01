## Summary

This draft analyzes the first formally unlocked L2/H1 prospective shadow cohort from PR #101 using the pre-registered contract and outcome-locked analyzer.

> Not submitted: fail-closed closeout stopped because the locked pre-reveal validator rejects the protocol-authorized `BOOTSTRAP_NOT_ESTIMABLE` path. This body is retained only as task-local evidence; no PR was opened.

## Frozen identity

- PR #101 head: `fbd4f3744e8b6d0448644c00cd8fdb1e8295902d`
- Protocol SHA-256: `e8ea8f3fda15ab81664829ea6f71fcb37f772ad613c13f61007856c16117791a`
- FORMAL_COLLECTION_LOCK SHA-256: `c30adc48099e8d7b90c980d84389cc1fa693cc1f87d3fc519089efb7cb81b756`
- Result commitment SHA-256: `3beb36d3e409483fa38b9a112e6070098309734045c3d7aae560e54ccd7b3ca2`
- Analysis execution lock SHA-256: `08cecef117031f599167ca944ba1ac9ac78da94a908a314ecf750729073e6d59`

## Formal result

- Intended/joined formal rows: 14,122 / 14,122
- Primary eligible: 0
- PASS / FAIL / UNKNOWN: 0 / 0 / 0 within the empty primary cohort
- Primary FAIL rate: not estimable
- UNKNOWN rate: not estimable
- Trial-cluster bootstrap: not estimable; 0 valid replicates after 100,000 zero-denominator draws
- L2 selected reach rate: 0 / 14,122
- Six logging-completeness rates: all 1.0
- Multi-candidate and selected-vs-native-nonselected analyses: not estimable

The result is `CASE_C_PRIMARY_NOT_ESTIMABLE`. This is a reachability/operational-opportunity finding, not a zero-risk, zero-FAIL, collision, progress, controller-efficacy, causal, real-time, or deployment result.

## Integrity and scope

The scientific outcome remained unread until all collection and result commitments were verified and the analyzer/validator hashes were frozen. The raw canonical step table stays server-only; this branch contains compact summaries and their manifest. No controller, instrumentation, map, candidate logic, L1/L2 certifier, trial, threshold, or raw formal artifact was modified or rerun.

## Decision

- Selected case: `CASE_C_PRIMARY_NOT_ESTIMABLE`
- Final decision: `PRIMARY_OPERATIONAL_OPPORTUNITY_NOT_ESTIMABLE`
- Only next task: `DIAGNOSE_L2_H1_PRIMARY_REACHABILITY_V1`

## Validation blocker

Twenty-one validator checks pass. `bootstrap_contract_exact` fails because the frozen validator unconditionally requires 10,000 valid replicates, while the frozen protocol explicitly requires `BOOTSTRAP_NOT_ESTIMABLE` after the maximum 100,000 draws if all replicates have zero denominator. The locked validator and numerical outputs remain unmodified after reveal.
