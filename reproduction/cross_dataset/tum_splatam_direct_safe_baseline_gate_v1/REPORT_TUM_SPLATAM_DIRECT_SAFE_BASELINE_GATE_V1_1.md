# TUM SplaTAM Direct-Safe Baseline Gate V1.1

## Protocol correction

The prior 908-center requirement is superseded: the canonical transforms contain 300 original-order map-aligned camera centers.  The prior V1 outputs were retained but not reused.

## Geometry gate

- endpoint float32-safe candidates: 195
- candidate pairs: 15374
- float64-qualified pairs: 23
- frozen registry SHA-256: `8857347130852ee25946f47575521024036663af80eb9b0ebe6e7d9a58b1f8b3`

## Original SAFER baseline

- DEVELOPMENT_PAIR (205->220, B1): `CBF_BOUNDARY_STALL`, steps=238
- HELDOUT_PAIR_1 (103->137, B2): `CBF_BOUNDARY_STALL`, steps=258
- HELDOUT_PAIR_2 (119->180, B3): `CBF_BOUNDARY_STALL`, steps=209
- HELDOUT_PAIR_3 (223->283, B4): `MAX_STEPS`, steps=800

## Decision

- baseline viability: `FAIL`
- final TUM decision: `CLOSE_TUM_NAVIGATION_BENCHMARK_KEEP_SAFETY_CASE_STUDY`
- certified robust overlaps: 0
- paired20 manifest SHA-256 unchanged: `380717f0ec39e0e422902573685f5a2838e78dd6efcce500ba71585efd3d82f6`

No Start-Safe, Risk-Aware, Recovery, V4-C, controller modification, Replica, or sequence-3 execution was performed by this task.
