## Summary

Adds an explicit Stonehenge V3 hard-radius runtime policy and wiring factory on exact base `606edd1c254f4ffaec48e0b84d8f5e5f29c039ec`.

- V3 hard runtime radius: `0.015 q`
- V3 runtime margin: `0 q`
- V3 runtime effective radius: `0.015 q`
- V3 `rho_seg`: `0 q`
- Historical `0.025 q` shell: diagnostic/design-reserve metadata only; runtime authority is false

The task-local factory defensively projects a V2-compatible config, reuses the frozen V2 `build_stack` composition, and fail-closed checks that the map adapter, CurrentCBFAdapter, L1/L2 segment backend, terminal certifier, and backup certifier share the single V3 hard-radius authority. Shared Active Runtime source and unified certificate mathematics are unchanged. Formal V2 evidence is immutable and unchanged.

CPU validation: V3 targeted tests 8/8, Active Runtime suite 179/179, unified certifier suite 33/33. No GPU, Smoke, Pilot, Formal, Reference, scientific oracle, or Official100 execution occurred.

`FINAL_STATUS=PASS_IMPLEMENT_AND_VALIDATE_V3_HARD_RADIUS_RUNTIME_WIRING_V1`

`FINAL_DECISION=ADVANCE_TO_ACTIVE_RUNTIME_SMOKE_V3_PROTOCOL_FREEZE`

Only next task: `FREEZE_ACTIVE_RUNTIME_SMOKE_V3_PROTOCOL`.
