## Scope

Freeze the post-repair engineering smoke protocol for certification–execution state identity repair V1. No GPU preflight, trial, controller/QP, PlantCommit, analyzer, Reference arm, Official100, or Formal execution occurred during this freeze.

## Frozen authority

- Implementation head: `546598a70e12fa99f9153f1927d0542ca27862b4`
- Repair specification: `77f8e52c2a2252fe651e4a13e3e30ada25168eb7`
- Runtime/scientific authority: `50cadfe614da70ce0345c4b1789c787dc529287e`
- Canonical transition: `canonical-transition:sha256:188eae47698febcd0d5492c1c0df2ea456a2fce23a83a616e28089f0e2f46d5d`
- Protocol freeze commit: `fc9757eb5f3fcfcc522ce67a443ff00bd13f00e0`
- Execution lock commit: the follow-up commit that adds the final `SMOKE_REPAIR_V1_EXECUTION_LOCK.json` identity; the protocol anchor is not amended.

## Frozen future smoke

- Trials/order: `[15, 45, 75]`, Dev15 only
- Limit: 500 completed public cycles per trial
- Serial, separate process, seed 0, physical GPU1
- Result root: `/disk1/zlab/v3_repair_records/cert_exec_identity_repair_smoke_v1_20260916`
- Geometry: 0.015 q hard radius, zero margin, zero rho; 0.025 q diagnostic-only with zero runtime authority
- Parent-owned fresh root, identity-bound child authorization, no automatic retry
- CPU synthetic mismatch guard: typed fail-closed, zero PlantCommit, one no-action evidence transaction

## Boundary

This smoke has no scientific efficacy claim or outcome gate. It does not alter or reinterpret the frozen paired result. `FROZEN_SCIENTIFIC_DECISION_REMAINS=FAIL_V3_HARD_SAFETY_GATE`.

Only next task after a complete freeze: `MANUALLY_START_FROZEN_CERTIFICATION_EXECUTION_STATE_IDENTITY_REPAIR_SMOKE_V1`.
