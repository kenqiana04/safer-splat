# Implement V3 Hard-Radius Runtime Wiring V1

`FINAL_STATUS=PASS_IMPLEMENT_AND_VALIDATE_V3_HARD_RADIUS_RUNTIME_WIRING_V1`

`FINAL_DECISION=ADVANCE_TO_ACTIVE_RUNTIME_SMOKE_V3_PROTOCOL_FREEZE`

## Answers

1. The sole V3 ACTIVE runtime hard-radius authority is **0.015 q**.
2. Does `0.025 q` retain runtime authority? **NO**.
3. Its role is the historical V2 diagnostic/design-reserve shell only.
4. L2, L3, backup, and terminal use the same hard-radius swept certifier. The frozen V2 constructor supplies one `segment_backend` to L1/L2 and one `swept` object to both `TerminalCertifier` and `BackupCertifier`; the V3 factory's bounded closure/object audit verifies those identities and the shared `0.015 q` value.
5. Was certificate mathematics rewritten? **NO**.
6. Was Formal V2 evidence modified? **NO**.
7. Were GPU, Smoke, Pilot, Formal, Reference, or Official100 runs executed? **NO**.
8. Was any physical-meter claim produced? **NO**.
9. Is the V3 runtime margin still `0.010`? **NO**. The V3 runtime reserve is `0 q`.
10. The next task is `FREEZE_ACTIVE_RUNTIME_SMOKE_V3_PROTOCOL`.

## Compatibility boundary

Legacy field suffix `_m` is retained for API compatibility only. For Stonehenge V3 these numeric values are interpreted in q, the Nerfstudio-scaled represented-map/query coordinate unit; no SI-meter interpretation is claimed.

The V3 package is additive. It creates a frozen task-local `V3AuthorityRegistry` derived from the unchanged V2 non-geometry authorities, temporarily injects that explicit registry only during the existing V2 stack builder call, restores the original constructor in `finally`, and validates the resulting object graph before returning it. No shared runtime source is modified.

## CPU evidence

- V3 targeted suite: 8/8 PASS.
- Active Runtime V2 suite: 179/179 PASS.
- Unified executable certifier suite: 33/33 PASS.
- Protected source diff: PASS; certificate mathematics, V2 Smoke/Pilot, and Formal V2 evidence are unchanged.
- Execution counts: GPU 0, Smoke 0, Pilot 0, Formal 0, Reference 0, Official100 0.
