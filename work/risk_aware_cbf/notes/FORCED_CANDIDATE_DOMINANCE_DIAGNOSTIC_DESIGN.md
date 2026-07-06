# Forced-Candidate Dominance Diagnostic Design

## Purpose

This task diagnoses why Adaptive V1 did not produce a measured candidate-count or runtime benefit after successful closed-loop integration. The focus is the forced-candidate dominance observed in the V1 candidate selector: final candidate sets are almost entirely explained by forced near, heading, and history candidates rather than by the adaptive risk-ranked budget.

This is a diagnostic and design task. It is not a new CBF theorem, not an official benchmark, and not a replacement for Certified Feasibility-Aware Start-Safe CBF, Discrete-Time Verification, or optional Predictive Recovery.

## Motivation

Prior Adaptive V1 evidence showed:

- `selected_K_applied_rate = 1.0`, so scheduler decisions are passed into the V1 budgeting wrapper.
- DT-risk windows receive larger scheduled budgets under `adaptive_balanced`.
- Collision, QP infeasibility, crash, and reported margin metrics did not degrade in the flight20 and targeted pilots.
- Measured candidate count remains nearly unchanged.
- `forced_candidate_fraction_mean = 1.0` in the targeted risk-window analysis.
- `budget_limited_candidate_count_mean = 0`.
- `heading_candidate_count` dominates `forced_near_candidate_count` and `history_candidate_count`.

The observed result supports risk-response integration, but not candidate-count or runtime improvement.

## Candidate Pipeline Hypothesis

The working hypothesis is:

- `selected_K` controls the V1 selector's `candidate_budget`.
- The selector first builds forced candidate sets: near-field candidates, heading-cone candidates, and spatially relevant history candidates.
- Forced candidates are unioned before the risk-ranked optional pool is filled.
- If the forced union already exceeds `candidate_budget`, the risk-ranked optional pool receives zero budget.
- The final unique candidate set is not capped after forced union.
- Heading candidates can be much larger than `selected_K`, so final candidate count is controlled by heading geometry rather than adaptive budget.
- `budget_limited_candidate_count = 0` is consistent with forced candidates already exceeding the scheduled budget.

This explains why `selected_K` can increase in DT-risk windows while measured final candidate count does not change.

## Diagnostic Questions

The diagnostic answers:

- Which layer does `selected_K` control?
- How large are forced candidates before and after union?
- Do heading candidates nearly cover the final candidate set?
- Are risk windows different from non-risk windows?
- Is forced-candidate dominance stronger in DT-warning or low-margin steps?
- Does unchanged candidate count explain why runtime does not improve?
- Does `budget_limited_candidate_count = 0` hold across targeted risk windows?
- Which candidate subsets change when `selected_K` increases?

## Design Candidates

These are design options only. They are not implemented as a new closed-loop method in this task.

### FC-A: Forced-Candidate-Aware Reporting Only

Add reports that explicitly separate forced near, heading, history, forced union, risk-ranked optional pool, and final unique count.

Pros: Low risk, paper-safe, directly explains the current Adaptive V1 limitation.

Risk: No algorithmic improvement.

Suitability: Good for the current paper as diagnostic evidence.

### FC-B: Per-Source Budget Accounting

Track source-specific budgets and utilization, including forced union size before optional fill and selected budget saturation.

Pros: Clarifies whether future gains are possible.

Risk: Still diagnostic unless connected to a selector change.

Suitability: Good follow-up instrumentation.

### FC-C: Heading Candidate Prioritization / Top-M Cap

Rank heading-cone candidates and cap them before union.

Pros: Directly targets the dominant source.

Risk: May remove safety-relevant constraints. Requires full-query fallback, DT verification, and closed-loop validation.

Suitability: Not safe as an unvalidated paper method; possible isolated offline sensitivity only.

### FC-D: Risk-Ranked Forced Candidate Pruning With Full-Query Fallback

Prune forced candidates using risk scores, but trigger full-query fallback under low margin, DT warning, selector uncertainty, or abnormal candidate count.

Pros: Potentially recovers efficiency while retaining conservative fallback.

Risk: Changes safety-critical candidate availability and needs dedicated validation.

Suitability: Possible future work or small isolated pilot, not automatic full100.

### FC-E: Two-Stage Selection

Keep a mandatory safety core and allocate an adaptive auxiliary pool around it.

Pros: Separates safety-preserving candidates from efficiency candidates.

Risk: Requires a principled definition of the mandatory core.

Suitability: Stronger design direction, but outside this diagnostic task.

### FC-F: Full-Query Fallback Only In Critical / Recovery-Support Mode

Allow more aggressive candidate reduction in nominal/caution modes and full-query fallback in high-risk modes.

Pros: Aligns compute cost with risk mode.

Risk: May miss relevant constraints before warning signals appear.

Suitability: Needs offline sensitivity first, then closed-loop smoke before any larger run.

## Recommended Next Action

If the diagnostic confirms forced-candidate dominance, keep Adaptive V1 as a support module or ablation and do not run full100 now. If a wrapper-level forced-candidate-aware cap appears plausible, the next step should be an isolated offline sensitivity analysis, clearly labeled as hypothetical accounting. Closed-loop validation and DT Verification would be required before any method claim.

