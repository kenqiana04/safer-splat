# V4-C Candidate-Family Contribution Audit Plan

## Purpose

This is a measurement specification, not an experiment result. It determines whether the original candidate families contribute unique feasible recoveries or merely add GSplat-query cost. It must retain compact aggregates only; raw controls, traces, JSONL, images, and per-step dumps are out of scope.

## Family Labels

Aggregate original source labels into `baseline` (base/nominal/scaled), `braking` (braking and brake-then-base), `repulsive` (repulsive, base-plus-repulsive, repulse-then-base), `goal_directed` (goal-directed and repulse-then-goal), `continuity` (previous/smooth), `random_around_base`, and `cem`. Each aggregate must preserve whether a family was enabled.

## Required Statistics

| Metric | Unit and denominator | Meaning | Guardrail |
| --- | --- | --- | --- |
| generated count | candidates per activated step | post-dedup candidates emitted by family | report zero when enabled but deduplicated away |
| feasible count | candidates with `min_h >= dt_margin` | local H-step feasibility contribution | not collision-free rate |
| selected count | selected candidates per family | direct selection contribution | one selected family at most per activation |
| recovery-success count | activations where selected family is feasible | selected family produces local recovery success | do not attribute success to unselected feasible families |
| mean selected min `h` | selected events for family | selected safety-field margin | `h` is not meters |
| mean progress delta | selected events for family | pre/post horizon goal-distance reduction | diagnostic, not planner quality |
| runtime contribution | family generation/evaluation wall time and fraction of activated runtime | cost attributable to inclusion | report measurement boundary and device |
| redundancy | feasible candidates not selected and never uniquely feasible | overlap with other families | requires same-step comparison |
| unique-success steps | activation where this is the only family with a feasible candidate | irreplaceable local feasibility | separate from selection count |

## Derived Decisions

For each family, compute selected share, feasible share, unique-success share, and runtime share. A family is a removal candidate only when its unique-success count is zero on the pre-registered bounded cohort and its removal does not change selected feasibility on that cohort. Low selection count alone is insufficient because a family may provide rare unique feasible recovery.

## Instrumentation Contract for a Later Task

The later task may add compact aggregate counters around original `generate_sequences` and `evaluate_sequences`; it must not alter candidate controls, RNG seeds, cost, ranking, or activation. It must report `unmeasured` rather than substituting zeros when a metric cannot be computed. It must separate baseline H-step violation, recovery failure, and collision.

## Stop Rule

Stop the family audit if aggregation requires raw sequence controls or traces, if it changes original selection behavior, or if instrumentation spills into CBF, GSplat, dynamics, planner, or R1 code.
