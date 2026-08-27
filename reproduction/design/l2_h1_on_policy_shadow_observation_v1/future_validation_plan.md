# Future Validation Plan

## Phase 0

Run schema positive/negative fixtures, canonical serialization round trips, immutable-copy tests, full-queue fault injection, serializer exception injection, worker crash injection, no-result-return static call-graph review, monotonic ID tests, map-manifest resolution, and candidate provenance validation. This phase is implementation QA, not research data.

## Phase 1

Run the pre-frozen OFF-vs-ON equivalence smoke and enforce `future_equivalence_gate_spec.md`. Do not combine its data with the primary cohort.

## Phase 2

Run the pre-frozen logging pilot and enforce `future_logging_completeness_gate.md`. Measure queue/drop behavior to choose a future frozen queue capacity; do not tune on L2 outcomes.

## Phase 3

Only after all gates pass, execute the separately authorized fixed manifest once. Validate each append-only log segment, manifest identity, denominator accounting, cluster labels, and recovery provenance.

## Phase 4

Lock raw evidence, run the pre-registered analysis, report numerator/denominator and cluster-aware uncertainty, and preserve failures/missingness.

This task executes none of these phases. Future validation never changes controller mathematics, candidates, map, seeds, trial order, or L2 authority.

**Scope:** DESIGN ONLY | NO ON-POLICY COLLECTION | NO CONTROLLER AUTHORITY | NO DECISION FEEDBACK | NO PERFORMANCE CLAIM.
