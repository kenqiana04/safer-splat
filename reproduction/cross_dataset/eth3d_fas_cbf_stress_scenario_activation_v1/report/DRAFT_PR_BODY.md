## Scope

PR #80 and its Case-B result are preserved. This continuation performed the preregistered plant-free activation search on the same frozen ETH3D map and failed closed before registry lock.

## Evidence

- candidate tuples: `200000`
- qualified strata: `{"G0": 11238, "G1_NEAR": 8988, "G1_PROJECTABLE": 42049, "G1_UNPROJECTABLE": 119759, "G2": 28213, "G3_ENDPOINT_ONLY": 2, "G3_ENDPOINT_UNSAFE": 0, "G3_MARGIN": 4394, "G4_RECOVERABLE": 99, "G4_UNRECOVERABLE": 24}`
- V1 semantic defect recorded without history rewrite
- H2 global constraint reduction reconciled against zero designated-G2 entry
- no map retraining, dataset switch, method tuning, smoke, or formal rollout

## Decision

- FINAL_STATUS: `NO_ETH3D_FROZEN_STATE_SET_SUFFICIENTLY_ACTIVATES_FAS_CBF_STAGE_H3_DISCRETE_TIME`
- FINAL_DECISION: `FREEZE_STRUCTURAL_ACTIVATION_LIMIT_AND_USE_EXISTING_CERTIFIED_MODULE_CASES`
- Only next task: `ASSEMBLE_FAS_CBF_MODULE_EVIDENCE_FROM_ETH3D_AND_EXISTING_FROZEN_CASES_V1`
