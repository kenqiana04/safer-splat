# Formal L2/H1 Prospective Shadow Cohort Protocol V1

## Frozen scope

This protocol freezes the complete Stonehenge `official100` cohort before any formal prospective shadow result exists. Collection is serial, uses a fresh process for every trial, preserves the frozen controller and zero-authority L2/H1 observer, and never changes trial order or count based on outcomes.

## Cohort and identity

- Trials: exactly 100 unique IDs, integer order `0..99`.
- Data role: `FORMAL_PROSPECTIVE_SHADOW_COHORT_V1` only.
- Run ID: `formal-v1-trial-{trial_id:03d}-attempt-{attempt_id}`.
- Prior equivalence, pilot, and historical replay rows are permanently excluded.
- Pilot trial IDs `10,30,50,70,90` are rerun formally with new FORMAL run IDs.

## Analysis unit and endpoint

The analysis unit is one selected/executed candidate-state-map tuple at one committed control step: `(run_id, trial_id, step_id, x_k, selected executed u_k, dt, map_authority_id)`. The primary denominator contains all eligible selected rows whose frozen shadow L1 status is PASS and whose L2 tri-state evaluation is complete; UNKNOWN remains in the denominator. The primary numerator is L2 FAIL.

## Collection and analysis separation

Collection-stage QC checks completeness, identity, type, health, termination, and raw-artifact hashes without aggregating or inspecting scientific PASS/FAIL/UNKNOWN distributions. Scientific analysis unlocks only after all 100 formal trials and a valid `FORMAL_COLLECTION_LOCK.json` exist.

## Stop rule

One automatic retry is allowed only for a fully recorded pre-data infrastructure failure before the first intended step and before any capture, result, or scientific row. Any post-data failure or per-trial hard-gate violation stops V1; partial evidence is retained and no rerun is mixed into V1.

## Claim boundary

The future analysis may quantify candidate-dependent future-segment shadow signal prevalence under the frozen controller. It cannot establish collision prevention, safety improvement, controller efficacy, recursive feasibility, safe stopping, real-time performance, deployment readiness, physical-world guarantees, or Core V2 superiority.
