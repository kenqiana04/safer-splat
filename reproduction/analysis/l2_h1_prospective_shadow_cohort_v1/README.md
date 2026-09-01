# L2/H1 Prospective Shadow Cohort Analysis V1

This directory contains the pre-registered, outcome-locked analysis of the formal 100-trial prospective shadow cohort collected under PR #101.

## Result at a glance

- Intended control steps: 14,122
- Joined formal rows: 14,122
- Primary-eligible rows: 0
- Selected case: `CASE_C_PRIMARY_NOT_ESTIMABLE`
- Scientific decision: `PRIMARY_OPERATIONAL_OPPORTUNITY_NOT_ESTIMABLE`

All six logging-completeness measures are 1.0. The zero primary denominator is therefore an operational reachability result, not evidence of missing logs and not evidence that L2 was safe or effective. No collision, progress, controller-efficacy, causal, real-time, or deployment claim is made.

The canonical per-step table remains server-only. Git contains only its manifest and compact, committed summaries. The two figures are presentation-only views generated from the locked compact results.

## Reproducibility boundary

The scientific analyzer and validator were frozen before the first real L2 status was read. After reveal, those locked files must not be edited. Synthetic contract tests are under `tests/`. The only authorized next scientific task is `DIAGNOSE_L2_H1_PRIMARY_REACHABILITY_V1`; it is not executed here.

## Fail-closed validation status

The locked validator passed 21 checks and failed `bootstrap_contract_exact`. The frozen protocol permits `BOOTSTRAP_NOT_ESTIMABLE` after 100,000 zero-denominator draws, but the pre-reveal validator implementation unconditionally requires 10,000 valid replicates. Because this core validator defect was discovered after outcome reveal, V1 closeout is stopped without editing the validator or falsifying the bootstrap result. See `VALIDATION_BLOCKER.json` and `validation_result.json`. No commit, push, or Draft PR is created from this blocked state.
