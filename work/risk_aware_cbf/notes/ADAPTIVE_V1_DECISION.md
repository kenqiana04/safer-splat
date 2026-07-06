# Adaptive V1 Decision

## 1. Continue

Current recommendation: `True`.

## 2. Enter Flight20

Recommendation: `True`. The next minimal experiment is a flight20 offline replay or a carefully smoke-tested closed-loop pilot, not full100 by default.

## 3. Enter Full100

Recommendation: `False`. Do not jump from offline replay/audit directly to full100; run flight20 or closed-loop pilot first.

## 4. Paper Method Role

Adaptive V1 should be framed as an efficiency / risk-response support module. Based only on offline replay, it should not be presented as a standalone main safety method.

## 5. If Not Main Method Yet

The current limitation is that offline replay does not change the executed trajectory and does not measure true closed-loop runtime or candidate counts. It verifies risk-responsive budget decisions, not closed-loop performance.

## 6. Next Minimal Experiment

Run flight20 first. If that remains stable, consider a closed-loop pilot with smoke gating before any full100 run.

## 7. Relationship To DT Verification

Adaptive V1 uses DT Verification warnings as feedback for budget scheduling. It does not replace DT Verification. DT Verification remains the independent sampled-data audit layer.

## 8. Relationship To Optional Predictive Recovery

Adaptive V1 can support optional Predictive Recovery by selecting recovery-support / fallback budget when recovery is triggered or risk is unresolved. It does not replace optional Predictive Recovery.

## 9. Recommended Paper Wording

- Adaptive V1 is a candidate budgeting and efficiency support module.
- Adaptive V1 increases candidate coverage in DT-warning or low-margin states.
- Offline replay results show risk-responsive scheduling behavior.
- Full-query verification and DT Verification remain required.

## 10. Forbidden Wording

- Do not claim Adaptive V1 alone guarantees safety.
- Do not claim a new CBF theorem.
- Do not describe margin violation as collision.
- Do not describe `min_safety_h` as meter clearance.
- Do not describe offline replay as closed-loop navigation.
- Do not say V4-C is an always-on default controller.

## Evidence Pointers

- Analysis directory: `work/risk_aware_cbf/results/adaptive_v1_budgeting_hotspot/analysis`
- Adaptive mode counts:

| run_label | mode | count | fraction |
| --- | --- | --- | --- |
| adaptive | caution | 406 | 0.371455 |
| adaptive | critical | 201 | 0.183898 |
| adaptive | nominal | 230 | 0.21043 |
| adaptive | recovery_support | 256 | 0.234218 |
