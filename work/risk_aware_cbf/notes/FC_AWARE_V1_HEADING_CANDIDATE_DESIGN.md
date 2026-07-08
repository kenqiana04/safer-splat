# FC-Aware V1 Heading Candidate Design

## 1. Purpose

This design shifts Adaptive V1 follow-up from mode-based `selected_K` tuning to forced-heading-aware candidate selection.

The goal is not to change the closed-loop selector in this phase. The goal is to test, by offline shadow accounting, whether source-aware heading prioritization could reduce final candidate count while preserving the mandatory safety core.

## 2. Motivation

Adaptive V1 risk response is established: DT-warning and low-margin windows receive larger `selected_K`, and `selected_K` is passed into the V1 candidate selector.

However, candidate-count reduction is not established:

- targeted risk-window selected_K ratio balanced/fixed: `2.884422`,
- targeted risk-window measured candidate-count ratio balanced/fixed: `0.999773`,
- forced candidate fraction mean: `1.0`,
- budget-limited candidate count mean: `0.0`,
- targeted risk-window heading fraction of final set: `0.990847`.

This means `selected_K` currently controls only the optional risk-ranked remainder after forced candidates are unioned. It does not cap the final unique candidate set. Heading candidates dominate the final set, so a candidate-efficiency follow-up should study heading-aware prioritization rather than continue tuning `selected_K` alone.

## 3. Candidate Source Taxonomy

- near candidates: mandatory safety core; keep all in the first FC-aware design.
- heading candidates: dominant forced source; candidate for source-aware ranking and top-M cap.
- history candidates: temporal support from high-active IDs; keep small cap or support-only policy.
- optional risk-ranked candidates: `selected_K`-controlled remainder after forced sources.

## 4. Proposed FC-aware Mechanism

First-version design:

1. Keep all near candidates.
2. Rank heading candidates with a risk-aware score.
3. Keep top-M heading candidates by scheduler mode.
4. Keep history candidates as a small support set or cap separately.
5. Fill optional risk-ranked candidates only after the source-aware forced set is constructed.
6. Guard any cap with DT Verification, full-query fallback, and rollback criteria.

This is a wrapper-level design idea, not an official core source change.

## 5. Heading Score Candidates

Possible ranking signals:

- heading alignment,
- distance to robot,
- low h / low safety margin proxy,
- previous active constraint membership,
- local density,
- angular sector coverage,
- temporal persistence,
- projected path proximity.

The current step logs do not contain per-heading-candidate IDs, so these ranking signals are future implementation requirements rather than measured recall evidence in the current shadow audit.

## 6. Mode-based Heading Budget

Candidate heading caps should be mode-dependent:

| mode | possible heading cap policy |
|---|---|
| nominal | small heading cap |
| caution | medium heading cap |
| critical | large heading cap |
| recovery_support | full heading set or full-query fallback |

The exact caps should not be claimed effective until per-candidate recall and closed-loop smoke validate them.

## 7. Fallback Conditions

Fallback to full heading / full-query should trigger when:

- DT warning persists,
- min_safety_h worsens,
- H-step margin worsens,
- QP becomes infeasible,
- selected candidate count is too low,
- heading score fields are missing,
- risk-window uncertainty is high,
- active constraint recall falls below threshold,
- near-only or capped-heading set fails basic feasibility checks.

## 8. Safety Constraints

No safety guarantee comes from a heading cap alone.

Required protections:

- near candidates are not capped in the first version,
- DT Verification remains the guard,
- full-query fallback remains available,
- full heading fallback remains available,
- closed-loop smoke is required before any benchmark,
- full100 is not justified from shadow accounting alone.

## 9. Decision Criteria

Continue FC-aware V1 only if shadow audit shows large theoretical candidate reduction and either per-candidate active/risk recall is high or additional logging can verify recall before closed-loop.

Freeze if active/risk recall is poor, unavailable without feasible logging, or if risk-window affected fraction is high without a conservative fallback design.

Do not proceed to full100 from shadow audit alone.
