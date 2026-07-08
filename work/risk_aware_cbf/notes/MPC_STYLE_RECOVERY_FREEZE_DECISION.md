# MPC-style Recovery Freeze Decision

## Decision Summary

The current primitive-sequence MPC-style Recovery profile is frozen.

| question | answer |
|---|---|
| Continue current primitive MPC-style profile? | No |
| Enter closed-loop smoke? | No |
| Enter flight20? | No |
| Enter full100? | No |
| Replace R4_H2_N64? | No |
| Use as paper main method? | No |
| Keep as optional extension / future work? | Yes |

## Evidence

The targeted offline pilot completed H2_N64 and H3_N64 over 199 trigger rows.

Both profiles had:

- success_count: 103
- improved_but_unresolved_count: 0
- no_improvement_count: 96
- failed_count: 0
- selected_exec_margin_violation_count: 96

H3 increased h improvement statistics, but it did not reduce the selected violation count.

## Main Failure Reasons

1. 96 selected H-step margin violations remain unresolved.
2. Runtime is high for an optional recovery module.
3. Selection is dominated by `nominal_hold` and `smooth_previous_nominal`.
4. H3 does not reduce selected violations relative to H2.
5. No closed-loop evidence exists.
6. The pilot is not directly comparable to R4_H2_N64.

## Runtime Note

Observed offline runtime:

- H2_N64 mean / p95 / max: 2.3606 / 2.4368 / 2.6446 s
- H3_N64 mean / p95 / max: 3.3939 / 3.4892 / 3.7861 s

This provides no runtime improvement claim. Do not compare directly against R4_H2_N64 as a benchmark because execution modes differ.

## Need For New MPC-style Design

No new MPC-style design is needed for the current small paper. A future version could explore obstacle-aware directions, safety-first selection, terminal escape objectives, and CBF-QP-in-the-loop rollout, but that should be separate future work.

## Next Step

Freeze the MPC-style Recovery line and return to FAS-CBF Method + Experiments writing.

Recommended hierarchy for the paper:

1. Start-Safe CBF as the main start-safe feasibility contribution.
2. Discrete-Time Verification as the main sampled-data risk contribution.
3. Existing V4-C / R4_H2_N64 as optional triggered recovery evidence.
4. Adaptive V1 as support / ablation.
5. MPC-style Recovery as future work / negative diagnostic.
