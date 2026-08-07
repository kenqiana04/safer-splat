# REPORT: Rank Core V1 actionable factors and select one bounded next step

## Result

`SELECT_CAUSAL_ARCHITECTURE_SPEC_AS_NEXT_STEP`

**Decision:** `FREEZE_IMPLEMENTATION_AND_WRITE_CORE_CAUSAL_ARCHITECTURE_SPECIFICATION_V1`

**Only next task:** `WRITE_CORE_CAUSAL_ARCHITECTURE_SPECIFICATION_V1`

## Frozen boundary

PR #84–#90 remain preserved Open Drafts. This is a decision analysis from frozen evidence only: formal B0–B3 runs=0; training=0; map/controller/method mutations=0; new data or datasets=0. The analysis preserves the PR #90 Case D conclusion and does not claim performance, navigation, or a new Core method.

## Action packages and scoring

| Action | Positive | Risk | Net |
| --- | ---: | ---: | ---: |
| A1 | 60 | 4 | 57.00 |
| A2 | 41 | 18 | 27.50 |
| A3 | 40 | 19 | 25.75 |
| A4 | 36 | 22 | 19.50 |
| A5 | 44 | 8 | 38.00 |

The scoring contract uses all 12 frozen positive items and eight risk items with `net=positive-0.75*risk`. Sunk cost is excluded. A1 is highest and, independently, the required common prerequisite for A2/A3/A4.

## Decisive evidence

- PR #90 proves the immediate position derivative with respect to `u_k` is zero; B1 must be given an explicit admission-versus-candidate-safety role before later gates can be interpreted.
- No frozen on-policy/intermediate logs, unused failed trajectories, or per-step official100 sequences were found; A2 remains data-dependent.
- The frozen A3 inventory has 0 legal eligible states: 22 are B2-primary committed and 58 are candidate-independently precluded.
- The OAT regime grid is not a real-system range contract; A4 cannot use artificial activation.
- A5 is deliberately rejected by D4, not selected merely because it is safe.

## Reviewer panel

Control/theory, robotics/system, and novelty/publication rank A1 first. Evaluation/statistics ranks A2 first due to the on-policy/power gap, but records A1 as a prerequisite. The 3:1 disagreement is preserved and resolved by REQUIRED edges, not suppressed.

## What this does not prove

It does not prove that Core V1 is correct, incorrect, competitive, safe for deployment, more active, generalizable, or ready for a paper. It does not implement a causal correction. It selects only the bounded specification task needed to distinguish a role-definition issue from a structural method mismatch.

## Anti-drift rule

The selected task may write a role/horizon/denominator specification only. It must not change B0–B3, create a controller branch, run a formal trial, use a new map/data/cohort, train, run a B3 oracle, or execute a configuration study.
