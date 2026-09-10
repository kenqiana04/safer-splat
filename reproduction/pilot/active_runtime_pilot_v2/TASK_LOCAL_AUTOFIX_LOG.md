# ACTIVE Runtime Pilot V2 task-local autofix log

## AF-001 — task-local import-path preflight

- Detected before any Pilot arm execution.
- The standalone ACTIVE child imported frozen runtime types before adding the
  frozen source checkout to `sys.path`.
- Fixed by adding the same frozen unified-certifier and checkout paths used by
  the Smoke runner before the import.
- Scientific inputs, runtime source, controller behavior, trial order, oracle,
  and outcomes were not touched.

Allowed fixes are limited to runner fields, summary/counter ordering, serialization,
task-local paths, subprocess environment/return-code handling, GPU cleanup
bookkeeping, parsers/reports, and summaries recoverable from immutable raw evidence.
Scientific inputs and runtime/production source are frozen.

## AF-002 — task-local remote launcher quoting

- Detected before the batch or any Pilot arm started.
- A PowerShell-to-SSH inline tmux command was parsed locally and never created a
  remote session.
- Replaced the inline command with a task-local server launcher whose arguments
  are literal and auditable.
- No runtime process, map, trial, arm, result, or scientific input was touched.

## AF-003 — source-relative map data path and partial-summary aggregation

- Trial 5 Reference stopped before step 0 because the frozen Nerfstudio config
  resolved `data/stonehenge/transforms.json` relative to the task launcher
  directory rather than the frozen source checkout.
- No action, state transition, or scientific result was produced.  The failed
  attempt is preserved under the server task's `autofix_attempts` directory.
- Fixed the task-local child working directory to match the validated Smoke
  execution context, and made partial-summary medians tolerate an empty timing
  list after a pre-step failure.
- Map/checkpoint, controller, dynamics, horizon, oracle, trial order, runtime
  source, and production source remain unchanged.

## AF-004 — descriptive aggregate completeness

- Detected after all 20 arms had completed and raw evidence was locked.
- The first aggregate omitted the pre-required per-role rates and paired
  count/mean/median/min/max fields, although all source values were present.
- Corrected only the task-local deterministic aggregate/report builder and
  regenerated compact aggregates from the immutable arm summaries.
- No rollout, oracle query, state, action, timing, controller, or scientific
  definition was changed or rerun.

## AF-005 — resolved-leaf min-clearance extraction

- Detected after all raw trajectories and Active traces were finalized.
- The first task-local oracle summary treated the conservative backend's
  diagnostic `global_lower` as a final clearance bound.  That value retains
  superseded parent-interval bounds, so one safe trial could show a negative
  reported minimum despite every segment resolving `CERTIFIED_SAFE`.
- Recomputed only posthoc oracle summaries from locked trajectories with the
  same frozen map query, 0.015/0.025 m radii, and 1-Lipschitz subdivision, using
  the minimum of resolved leaf bounds.  No arm, state, action, runtime trace,
  or scientific threshold was changed or rerun.
