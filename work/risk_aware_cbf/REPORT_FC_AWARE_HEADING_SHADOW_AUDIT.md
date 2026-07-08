# FC-Aware V1 Heading Candidate Shadow Audit

## 1. Purpose

This report evaluates whether Adaptive V1 should move from selected_K-only candidate budgeting toward forced-heading-aware candidate selection.

This is an offline shadow audit. It is not a closed-loop result, not a full100 benchmark, and not a runtime or safety guarantee.

## 2. Background

Adaptive V1 established risk-responsive scheduling: DT-warning and low-margin windows receive larger `selected_K`, and `selected_K` is passed into the V1 candidate selector.

However, candidate-count reduction did not materialize because final candidate sets are forced-candidate dominated:

- targeted risk-window selected_K ratio balanced/fixed: `2.884422`
- targeted risk-window measured candidate-count ratio balanced/fixed: `0.999773`
- forced candidate fraction mean: `1.0`
- budget-limited candidate count mean: `0.0`
- targeted risk-window heading fraction of final set: `0.990847`

This means selected_K controls the optional risk-ranked remainder, while forced heading candidates dominate the final unique candidate set.

## 3. Candidate Pipeline Inspection

Read-only inspection output:

- `work/risk_aware_cbf/results/fc_aware_heading_shadow_audit/heading_pipeline_inspection.md`
- `work/risk_aware_cbf/results/fc_aware_heading_shadow_audit/heading_pipeline_inspection.json`

Key findings:

- heading candidates are generated in `V1CandidateSelector.select`,
- heading candidates are selected by heading distance and heading cosine alignment thresholds,
- heading candidates are forced through `forced = forced_near | forced_heading | forced_history`,
- `selected_K` is passed into `selector.candidate_budget`,
- `selected_K` only limits optional risk-ranked fill when `forced_count < candidate_budget`,
- final union has no post-cap,
- candidate scores exist for optional risk-ranked sorting, but heading top-M selection would need wrapper logic and per-candidate logging.

## 4. FC-Aware Design

The first FC-aware design should be conservative:

- keep all near candidates,
- rank heading candidates and keep top-M by mode,
- keep history as support or apply a small independent cap,
- fill optional risk-ranked candidates after source-aware forced selection,
- trigger full heading / full-query fallback when DT Verification or margin checks indicate risk.

This design does not modify official source in the current phase.

## 5. Shadow Audit Setup

Inputs:

- `work/risk_aware_cbf/results/adaptive_v1_targeted_dt_risk_closed_loop/`
- `work/risk_aware_cbf/results/adaptive_v1_flight20_closed_loop/`
- `work/risk_aware_cbf/results/forced_candidate_dominance/`

Caps tested:

- 2000
- 4000
- 8000
- 12000
- 16000

Accounting:

- aggregate source counts only,
- near candidates kept all,
- history uncapped,
- hypothetical final count computed from near + capped heading + history, clipped by original final count,
- source overlap cannot be reconstructed,
- per-candidate recall is unavailable.

Because candidate IDs, retained heading IDs, active IDs, and low-h candidate IDs are not present in the current step CSVs, active/risk recall cannot be measured.

## 6. Results By Heading Cap

Targeted risk-window tradeoff:

| heading cap | original final mean | hypothetical final mean | reduction ratio mean | affected steps fraction | risk-window affected fraction | DT-warning affected fraction | low-margin affected fraction | safety concern |
|---:|---:|---:|---:|---:|---:|---:|---:|---|
| 2000 | 24914.66 | 2536.15 | 0.897607 | 1.0 | 1.0 | 1.0 | 1.0 | true |
| 4000 | 24914.66 | 4536.15 | 0.816687 | 1.0 | 1.0 | 1.0 | 1.0 | true |
| 8000 | 24914.66 | 8536.15 | 0.654847 | 1.0 | 1.0 | 1.0 | 1.0 | true |
| 12000 | 24914.66 | 12536.15 | 0.493007 | 1.0 | 1.0 | 1.0 | 1.0 | true |
| 16000 | 24914.66 | 16536.15 | 0.331167 | 1.0 | 1.0 | 1.0 | 1.0 | true |

All loaded balanced steps, including flight20 and targeted:

| heading cap | original final mean | hypothetical final mean | reduction ratio mean | affected steps fraction |
|---:|---:|---:|---:|---:|
| 2000 | 23563.39 | 2137.81 | 0.905604 | 1.0 |
| 4000 | 23563.39 | 4137.81 | 0.816903 | 1.0 |
| 8000 | 23563.39 | 8130.08 | 0.640720 | 0.993822 |
| 12000 | 23563.39 | 12090.49 | 0.468674 | 0.988056 |
| 16000 | 23563.39 | 16011.85 | 0.299647 | 0.964168 |

The accounting headroom is large, but every targeted risk-window row is affected by every tested cap.

## 7. Risk-Window Analysis

In targeted risk windows, heading candidates are the dominant source and every tested cap changes the aggregate final candidate accounting.

This supports the bottleneck diagnosis: heading candidates are the right source to inspect if candidate-count reduction is desired.

It does not support immediate closed-loop capping because:

- risk-window affected fraction is `1.0`,
- DT-warning affected fraction is `1.0`,
- low-margin affected fraction is `1.0`,
- per-candidate active/risk recall is unavailable,
- source overlaps cannot be reconstructed.

Therefore, the next step is logging, not closed-loop smoke.

## 8. Safety And Verification Concerns

Heading cap may remove safety-relevant candidates. The shadow audit cannot determine which heading candidates are active, near-active, low-h, or needed by the QP.

Required safeguards before any wrapper-level closed-loop test:

- keep all near candidates,
- full heading fallback,
- DT Verification guard,
- full-query fallback,
- rollback if margin worsens,
- active/risk recall logging,
- closed-loop smoke before any broader benchmark.

No safety guarantee is claimed from this audit.

## 9. Decision

| question | decision |
|---|---|
| Continue FC-Aware V1? | Yes, design/logging follow-up only |
| Recommend wrapper-level closed-loop smoke now? | No |
| Recommend full100 now? | No |
| More promising than selected_K-only Adaptive V1? | Yes as a candidate-count lever, but unvalidated |
| Minimum next step | Add per-candidate logging and recall audit |

FC-aware heading selection is more structurally aligned with the measured bottleneck than selected_K-only scheduling. But the current evidence is aggregate-only and risk-window affected fraction is high, so closed-loop smoke should wait until recall logging exists.

## 10. Limitations

- Offline shadow audit only.
- Aggregate accounting may not preserve source overlap.
- Per-candidate recall is unavailable.
- No closed-loop safety evidence.
- No runtime evidence.
- No new theorem.
- `h` / `min_safety_h` is not metric clearance.
- Margin violation is not collision.
- No official core source was modified.
