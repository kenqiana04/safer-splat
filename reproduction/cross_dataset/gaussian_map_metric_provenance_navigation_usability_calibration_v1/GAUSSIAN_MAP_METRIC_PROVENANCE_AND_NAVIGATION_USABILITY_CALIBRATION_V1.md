# Gaussian Map Metric Provenance and Navigation Usability Calibration V1

## Authority and scope

This task is a read-only historical audit and retrospective-evaluation protocol-design task. Its frozen upstream is PR #74 at `26695aed7dec199c40ef7977e1885fdc2d2ecca1`. PRs #68 through #74 and every historical map, checkpoint, canonical array, report, JSON record, controller, route registry, and result remain immutable.

The audit may read Git history, authoritative server records, retained map artifacts, held-out summaries, reference geometry, and route contracts. It may generate compact diagnostics and documentation. It may not download a dataset or map, train or resume a map, tune a model, filter or transform a map, run a controller or planner, or reinterpret a historical status as a new pass.

## Frozen scientific rules

- The renderer acceptance threshold, global coverage, and conditional depth error are separate quantities.
- Rejected support is `UNKNOWN`, never automatically `FREE`.
- Fixed alpha reporting grid: `{0.05,0.10,0.20,0.30,0.40,0.50,0.60,0.70,0.80,0.90,0.95}`.
- Fixed geometry reporting tolerances: `{0.01,0.02,0.03,0.05,0.10,0.20}` metres. These are reporting points, not pass gates.
- A complete curve is reported only from retained observations or a read-only rerender under identity-preserving semantics. Missing evidence is labelled `NOT_EVALUABLE`; it is never interpolated.
- The positive calibration control is Replica GT-derived FINE. TUM and Replica Splatfacto are negative controls. TUM SplaTAM, TUM Gaussian-SLAM, Replica SplaTAM, and ARKitScenes M1 are audit candidates and cannot fit a gate that makes themselves pass.
- Universal navigation hard gates are restricted to integrity requirements and route-conditioned physical requirements. Project heuristics and unresolved thresholds are never universal navigation hard gates.
- One-sided dangerous map error is `e_plus=max(0,d_map-d_ref)`. A route is only physically supportable when an explicitly identified upper bound on `e_plus` in the swept route tube does not exceed the remaining physical budget.
- Single-seed evidence qualifies only the frozen map instance, not algorithmic stability.

## Frozen legacy interpretation

`LEGACY_FORMAL_STATUS=NO_ARKITSCENES_M1_LEARNED_GAUSSIAN_MAP_QUALIFIED_UNDER_FROZEN_CONTRACT`

`LEGACY_INTERPRETATION=FAILED_GLOBAL_DENSE_QUALIFICATION_UNDER_LEGACY_UNCALIBRATED_COVERAGE_GATE`

`NAVIGATION_USABILITY=NOT_YET_DETERMINED_UNDER_PROTOCOL_V2`

## Expected closeout

`FINAL_STATUS=PASS_GAUSSIAN_MAP_METRIC_PROVENANCE_AND_NAVIGATION_USABILITY_CALIBRATION_V1`

`FINAL_DECISION=FREEZE_LAYERED_GAUSSIAN_MAP_EVALUATION_PROTOCOL_V2`

`GLOBAL_NUMERIC_GATE_DECISION=NO_UNIVERSAL_NUMERIC_GATE_JUSTIFIED_BY_CURRENT_EVIDENCE`

`ONLY_NEXT_TASK=RETROSPECTIVE_REQUALIFY_EXISTING_GAUSSIAN_MAPS_UNDER_LAYERED_PROTOCOL_V2`
