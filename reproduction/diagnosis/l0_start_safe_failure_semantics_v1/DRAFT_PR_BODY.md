# Summary

Diagnoses the frozen `14,122 / 14,122` L0 `FAIL` outcome without modifying any V1 input, row, result, controller, map, threshold, radius, margin, or certifier.

## Frozen upstream

- PR #104: Open Draft
- branch: `diagnose-l0-shadow-certifier-semantics-v1`
- exact head: `14c844adeda8a0e8eb418abcdbaac62c701e2910`
- formal facts preserved: 14,122 rows; 0 PASS; 14,122 FAIL; 0 UNKNOWN

## Answer-first diagnosis

The source formula is internally consistent. For each loaded Gaussian, the query computes signed squared point-to-ellipsoid clearance and subtracts the effective radius squared; the FULL adapter takes the minimum over all Gaussians. Finite `h>=0` maps to PASS and finite `h<0` to FAIL.

The material mismatch is between geometry authorities:

- frozen controller radius: `0.015`
- shadow L0 robot radius: `0.10`
- shadow L0 safety margin: `0.01`
- shadow L0 effective radius: `0.11`

The query point, map checkpoint, Gaussian set, filtering behavior, ellipsoid math, minimum aggregation, and sign convention are otherwise shared.

Static evidence did not contain formal raw `h`, so the protocol-fixed 15 existing states were selected before `h` was read. The exact frozen L0 query produced:

- n: 15
- h min / median / max: `-0.0113929091 / -0.0103109423 / -0.00663070148`
- all negative: true
- raw clearance distance min / median / max: `0.0265912 / 0.0422973 / 0.0739547`

Every sentinel's raw clearance is greater than `0.015` and less than `0.11`. This directly demonstrates the contract split on the bounded diagnostic set. It is not a prevalence estimate for all formal rows.

## Decision

- root class: `SS-F5 — L0_CONTROLLER_GEOMETRY_CONTRACT_MISMATCH`
- `FINAL_STATUS=PASS_L0_START_SAFE_FAILURE_SEMANTICS_DIAGNOSIS_V1`
- `FINAL_DECISION=FREEZE_L0_FAILURE_MECHANISM_AND_AUTHORIZE_MINIMAL_TARGETED_NEXT_STEP`
- only next task: `DESIGN_L0_CONTROLLER_GEOMETRY_CONTRACT_V2`

No correction is included or authorized by this PR.
