# FAS-CBF Methodology Completion Check

## Certified Feasibility-Aware Start-Safe CBF

Closed for dense flight reproduction-side evidence: initial certification, near-unsafe / unsafe diagnosis, active-set verified projection, full GSplat query verification, and post-repair navigation are reported separately from original benchmark navigation.

## Discrete-Time Verification

Closed for dense flight consolidation: verification-only audit is available, H=1/H=2/H=3 ablation is reported, H2/H3 overlap is quantified, margin violation is separated from collision, and the trigger rule is specified.

## Optional Predictive Recovery

Closed as an optional module: H3_N128 remains the robust reference, R4_H2_N64 is the dense-flight practical configuration, and V4-C is warning/on-margin triggered rather than an always-on default controller.

## Adaptive V1 Candidate Budgeting

Closed as support / ablation for the current paper. Adaptive V1 shows risk-responsive budget scheduling and closed-loop integration, but it does not support a candidate-count reduction claim or runtime improvement claim in the current implementation.

Final status:

- Adaptive V1 role: support module / ablation, not main contribution.
- Adaptive V1 efficiency claim: not supported.
- Forced-candidate dominance: confirmed, especially heading candidates.
- Forced-candidate-aware budgeting: future work / separate design only.
- Full100 for Adaptive V1 now: not recommended.

## Paper Readiness

Current recommendation: PROCEED_TO_METHOD_AND_EXPERIMENT_WRITING.

If entering writing, the module hierarchy should be:

1. Certified Feasibility-Aware Start-Safe CBF as the start-safe navigation foundation.
2. Discrete-Time Verification as the independent sampled-data risk detector.
3. Optional Predictive Recovery as the triggered response to DT warning/on-margin risk.
4. Adaptive V1 only as a risk-response candidate-budgeting ablation with an explicit forced-candidate dominance limitation.

## Claim Boundary

No new CBF theorem is claimed. `min_safety_h` is the repository GSplat ellipsoid safety h value, not meter clearance. Synthetic starts are not official benchmark starts. Post-repair navigation is not original benchmark navigation. Adaptive V1 does not guarantee safety, does not replace DT Verification, and does not prove runtime or candidate-count improvement. Official SAFER-Splat baseline source is not modified.
