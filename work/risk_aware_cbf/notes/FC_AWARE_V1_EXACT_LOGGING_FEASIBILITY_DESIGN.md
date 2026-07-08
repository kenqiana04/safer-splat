# FC-Aware V1 Exact Logging Feasibility Design

## Purpose

This note defines a feasibility probe for exact FC-Aware V1 logging. The probe checks whether active constraint IDs, per-candidate safety `h` values, low-`h` IDs, heading distance / cosine, and retained top-M heading IDs can be recorded without modifying official SAFER-Splat source.

This is not a capped closed-loop experiment, not a full100 benchmark, and not a new CBF theorem.

## Motivation

The previous FC-Aware audits established the following:

- candidate source IDs are reconstructable exactly from saved states and the V1 selector formulas,
- forced heading candidates dominate the final candidate union,
- active constraint IDs are not available in saved logs,
- per-candidate `h` values and low-`h` candidate IDs are not available in saved logs,
- active and low-`h` recall are unavailable,
- no heading cap or ranking strategy can be recommended for closed-loop use yet.

Before FC-Aware V1 can move beyond diagnostic / design evidence, the logging path must show whether exact recall inputs can be obtained without touching `cbf/`, `splat/`, `ellipsoids/`, `dynamics/`, or `run.py`.

## Required Exact Fields

| field | purpose |
|---|---|
| `final_candidate_ids` | final selector union before CBF-QP |
| `heading_candidate_ids` | forced heading source set |
| `near_candidate_ids` | forced near source set |
| `history_candidate_ids` | forced active-history source set |
| `active_constraint_ids` | solver-active QP constraint IDs mapped to global Gaussian IDs |
| `candidate_h_values` | per-candidate repository GSplat safety `h` values |
| `low_h_candidate_ids` | candidate IDs below a declared low-`h` threshold |
| `heading_distance_values` | distance from robot to heading candidates |
| `heading_cosine_values` | heading alignment cosine for heading candidates |
| `retained_heading_topM_ids` | retained heading IDs under candidate caps / ranking strategies |
| `ranking_score_values` | exact scores used for ranking audit variants |

## Feasibility Categories

| field | category | exactness condition |
|---|---|---|
| `final_candidate_ids` | reconstructable offline / wrapper instrumentation | exact if saved state, nominal control, selected_K, selector thresholds, risk table, and GSplat means match the run |
| `heading_candidate_ids` | reconstructable offline / wrapper instrumentation | exact under the same selector-formula match |
| `near_candidate_ids` | reconstructable offline / wrapper instrumentation | exact under the same selector-formula match |
| `history_candidate_ids` | reconstructable offline / wrapper instrumentation | exact if active-frequency table and selected_K-derived history size match the run |
| `heading_distance_values` | reconstructable offline | exact from saved state and GSplat means |
| `heading_cosine_values` | reconstructable offline | exact from saved state, nominal control, and GSplat means |
| `retained_heading_topM_ids` | reconstructable offline | exact for ranking strategies whose scores are logged or reconstructable |
| `candidate_h_values` | available with wrapper instrumentation | exact for the queried candidate set if the wrapper captures `GSplatLoader.query_distance` output |
| `low_h_candidate_ids` | available with wrapper instrumentation | exact under the declared threshold if `candidate_h_values` are captured |
| `active_constraint_ids` | available only if wrapper captures solver dual/slack with constraint-ID mapping | exact for the replayed QP rows if solver dual/slack and mapped constraint IDs are captured; unavailable in saved logs |

## Probe Scope

The no-intervention probe may replay a very small number of saved states and log extra fields. It must not:

- alter candidate selection,
- alter controller output,
- integrate a new trajectory,
- run a capped heading variant,
- run full100,
- enable V4-C recovery,
- modify official core source.

For active IDs, the probe may use wrapper-only instrumentation around the QP solve. If the solver dual/slack cannot be captured without editing official source, active IDs remain unavailable and must not be treated as exact.

For low-`h` IDs, the probe may query `h` values for the final candidate set only. The logged `h` values are repository GSplat ellipsoid safety values, not metric clearance.

## Decision Logic

| condition | next decision |
|---|---|
| active IDs and low-`h` IDs both exact with acceptable overhead | continue exact recall audit; still do not run full100 |
| low-`h` IDs exact but active IDs not exact | continue a low-`h` recall audit only; do not run capped closed-loop |
| active IDs exact but low-`h` IDs not exact | continue active recall logging only; do not run capped closed-loop |
| neither active IDs nor low-`h` IDs exact | freeze FC-Aware V1 as future work / diagnostic insight |
| logging overhead too high | keep FC-Aware V1 as future work, even if exact fields are technically obtainable |

Closed-loop smoke requires a separate decision after exact recall evidence. Full100 is out of scope for this probe.
