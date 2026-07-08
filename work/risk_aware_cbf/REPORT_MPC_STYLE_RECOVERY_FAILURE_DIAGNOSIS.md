# MPC-style Recovery Failure Diagnosis

## 1. Purpose

This report diagnoses why the primitive-sequence MPC-style Recovery targeted offline pilot should not enter closed-loop smoke, flight20, or full100 in its current form.

The report freezes the current evidence chain. It is not a new recovery method proposal and does not introduce additional experiments.

## 2. Context

The paper methodology remains:

1. Certified Feasibility-Aware Start-Safe CBF.
2. Discrete-Time Verification.
3. Optional triggered Predictive Recovery.

MPC-style Recovery is only an optional extension / future-work direction. It is not the main method, not a standalone safety guarantee, not a new CBF theorem, not a replacement for Start-Safe CBF, not a replacement for DT Verification, not a replacement for CBF-QP filtering, and not a replacement for existing V4-C.

Margin violation is not collision. The safety value `h` / `min_safety_h` is the repository GSplat ellipsoid safety value, not meter clearance.

## 3. Prior Targeted Pilot Summary

The prior pilot was an offline evaluator over targeted DT-risk trigger states:

- source: `adaptive_v1_targeted_dt_risk_closed_loop` step CSV plus target windows,
- trigger rows: 199,
- profiles: `primitive_h2_n64` and `primitive_h3_n64`,
- sequence sanity check: passed,
- dry-run: passed,
- H2 smoke: passed,
- targeted H2_N64: completed,
- targeted H3_N64: completed,
- analyzer: completed,
- official core source changes: none.

This was not closed-loop and not full100. It has no collision or QP-infeasible outcomes.

Summary:

| profile | triggers | success | improved but unresolved | no improvement | failed | base violations | selected violations | runtime mean / p95 / max |
|---|---:|---:|---:|---:|---:|---:|---:|---|
| `primitive_h2_n64` | 199 | 103 | 0 | 96 | 0 | 101 | 96 | 2.3606 / 2.4368 / 2.6446 |
| `primitive_h3_n64` | 199 | 103 | 0 | 96 | 0 | 108 | 96 | 3.3939 / 3.4892 / 3.7861 |

The result is not directly comparable to V4-C R4_H2_N64 because R4_H2_N64 is closed-loop full100 / hotspot evidence, while this pilot is offline targeted replay.

## 4. Success Taxonomy Analysis

Both profiles have the same taxonomy:

- success: 103
- improved_but_unresolved: 0
- no_improvement: 96
- failed: 0

The absence of `improved_but_unresolved` is informative. The primitive library either finds a sequence that remains above the DT margin, or it fails to improve the minimum H-step safety value at all. There is little evidence of gradual recovery behavior in hard states.

This suggests that the current primitive sequence set is missing useful intermediate avoidance behavior. It also suggests that simply selecting from short nominal, smoothing, brake, lateral, and vertical primitives does not create a meaningful escape trajectory in the deepest low-margin states.

## 5. Sequence Selection Analysis

Dominant H2 selections:

- `nominal_hold`: 124
- `smooth_previous_nominal`: 60
- `deceleration_0.5`: 8
- `previous_safe_hold`: 3

Dominant H3 selections:

- `nominal_hold`: 121
- `smooth_previous_nominal`: 54
- `deceleration_0.5`: 8
- `deceleration_0.25`: 6
- `previous_safe_hold`: 4

The search frequently selected nominal or smoothed nominal controls. In unresolved rows, `nominal_hold` accounts for the no-improvement cases in both H2 and H3.

Likely interpretations:

- the primitive library did not include a better safety-improving action for those states,
- the low-margin states are already too deep for the current primitive scales over H=2/H=3,
- the objective can prefer nominal-like actions when no candidate clears the margin,
- the safety penalty is not strong enough to create a lexicographic safety-first choice in unresolved states,
- obstacle-aware recovery directions are missing.

## 6. Failure Concentration

Selected margin violations are concentrated in the same trials for H2 and H3:

| profile | trial 12 | trial 13 | trial 14 |
|---|---:|---:|---:|
| `primitive_h2_n64` | 42 | 44 | 10 |
| `primitive_h3_n64` | 42 | 44 | 10 |

Trials 7 and 9 were fully successful. The failures are concentrated in trials 12, 13, and 14, which are deeper low-margin cases.

This argues against more broad full100 experimentation for the current profile. If a future MPC-style design is revisited, the useful target is a small hard-case set from trials 12/13/14, not full100.

## 7. Horizon Analysis

H3 improves h statistics but not the failure set:

| metric | H2_N64 | H3_N64 |
|---|---:|---:|
| h_improvement_mean | 1.39534e-07 | 8.50932e-07 |
| h_improvement_p95 | 4.71063e-07 | 3.22027e-06 |
| selected violation count | 96 | 96 |
| no_improvement count | 96 | 96 |

The longer horizon improves average and p95 h improvement, but it does not reduce the number of unresolved selected margin violations. Therefore, simply increasing H from 2 to 3 is not enough to solve the hard cases.

H3 also increases runtime substantially, so it does not justify closed-loop escalation.

## 8. Runtime Analysis

Observed offline per-trigger runtime:

- H2_N64 mean: 2.3606 s
- H2_N64 p95: 2.4368 s
- H3_N64 mean: 3.3939 s
- H3_N64 p95: 3.4892 s

Existing V4-C closed-loop references:

- H3_N128 full100: 0.170388 / 0.702523 / 1.638351 runtime mean / p95 / max
- R4_H2_N64 full100: 0.095952 / 0.309428 / 0.654511 runtime mean / p95 / max

The modes are not directly comparable, but qualitatively the primitive MPC-style evaluator has no runtime advantage signal. It is not a practical recovery module in the current implementation.

## 9. Relationship To V4-C

The current MPC-style result cannot be fairly compared to R4_H2_N64 because it is offline targeted replay, not closed-loop full100 execution.

However, the qualitative evidence does not support replacing R4_H2_N64:

- H2/H3 both leave 96 selected margin violations,
- H3 does not reduce the unresolved set,
- runtime is high,
- selection is dominated by nominal-like sequences,
- no closed-loop evidence exists.

R4_H2_N64 remains the current practical optional recovery reference. H3_N128 remains the robust reference. The primitive MPC-style line should be treated as future work / negative diagnostic evidence.

## 10. Possible Causes

Likely failure causes:

1. Primitive action set is too weak.
2. Lateral / vertical scales are too small for deep low-margin states.
3. Cost function can favor `nominal_hold` when no candidate clears the margin.
4. Safety penalty is not strong enough or not lexicographic.
5. H2/H3 horizons are still too short.
6. Target states are already deep low-margin cases.
7. Offline replay states and controls do not match closed-loop recovery dynamics exactly.
8. Sequence search does not include CBF-QP response in the rollout loop.
9. There is no terminal escape objective.
10. There is no adaptive obstacle-aware direction generation.

## 11. Future Improved MPC-style Version

This is future work only and is not needed for the current small paper.

A stronger version would likely need:

- obstacle-gradient-aware primitive directions,
- safety-first / lexicographic selection,
- stronger safety penalty and terminal escape objective,
- adaptive sequence scales,
- longer horizon with pruning,
- warm-start from V4-C R4 actions,
- CBF-QP-in-the-loop rollout,
- early rejection and vectorized safety queries,
- evaluation only on the hard failure cases before any broader benchmark.

## 12. Decision

Current primitive MPC-style profile: freeze.

| question | decision |
|---|---|
| Continue this primitive profile? | No |
| Closed-loop smoke now? | No |
| Flight20 now? | No |
| Full100 now? | No |
| Replace R4_H2_N64? | No |
| Paper main method? | No |
| Future work / optional extension? | Yes |

The main paper should return to Start-Safe CBF + DT Verification + existing optional V4-C writing.

## 13. Limitations

- Targeted offline replay only.
- Not closed-loop.
- Not full100.
- No collision or QP outcomes.
- No new theorem.
- Margin violation is not collision.
- `h` is not meter clearance.
- No official core source modification.
