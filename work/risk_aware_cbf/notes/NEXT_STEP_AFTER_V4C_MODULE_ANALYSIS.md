# R-V4C-1 Held-Out Activated Cohort Execution Plan

**Goal:** Validate the frozen hierarchical V4-C V0 only on the 16 held-out flight H3_N128 activation trials defined by the original full100 comparator, with a paired same-state gate before sequential active A/B.

**Constraints:** V0 evaluator, candidate-family accounting, original V4-C/V1/V4B runners, CBF, GSplat, dynamics, and `run.py` remain read-only. The cohort is derived solely from the original comparator artifact; development trials 12, 13, and 14 are excluded from all formal held-out metrics.

## Steps

- [x] Create the held-out branch from `v4c-hierarchical-candidate-evaluation-v0` at `11e2a4f8c49266a11c4c178e947b46ee70612d99` and create a checkpoint.
- [ ] Add a comparator-only inventory selector with hard assertions for 100 trials, 19 activated trials, 236 activations, 16 held-out trials, fixed controls, and preregistered order.
- [ ] Add compact held-out paired-shadow auditing that delegates candidate generation and selection to frozen original/V0 functions and gates active A/B.
- [ ] Add sequential held-out active A/B aggregation, guardrails, result tables, metrics, and report generation without raw controls or traces.
- [ ] Run the frozen 16-check contract, comparator-derived inventory, paired audit, and only then active A/B on 4090 in tmux.
- [ ] Update permitted decision/material files, verify forbidden-path/raw-artifact absence, commit, push, create a draft PR, and copy the final REPORT Markdown to `C:\\Users\\zlab\\Desktop\\REPORT`.

## Verification

- The inventory validates the comparator totals before any hierarchical outcome is inspected.
- The paired gate requires all 16 held-out trials, zero feasibility regression, state isolation, unchanged formal comparator control, Stage-B equivalence when entered, and positive median runtime reduction.
- Active A/B follows the immutable ascending-ID alternating order, includes exactly 38 runs, and reports all safety, runtime, progress, candidate-family, Stage-B, and nonactivated-control guardrails.
