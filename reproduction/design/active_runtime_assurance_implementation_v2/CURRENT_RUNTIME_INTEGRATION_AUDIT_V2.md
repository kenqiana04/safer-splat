# Current Runtime Integration Audit V2

## Exact static seams

| Required fact | Frozen source | Design conclusion |
|---|---|---|
| state `x_k` | `run.py:100-104,118-132` | Local 6-vector, position first then velocity; directly available to an additive driver. |
| goal | `run.py:92-104` | Frozen start/goal generation is reusable and can receive stable trial/start/goal IDs. |
| desired command `u_des` | `run.py:118-127` | PD reference, componentwise clamped; it is not certified and is not an alternative. |
| primary proposal | `run.py:132`; `cbf/cbf_utils.py:125-142` | Successful Clarabel CBF-QP result; solver failure currently returns `u_des`, which the V2 adapter must reject as `NO_PRIMARY_PROPOSAL`. |
| actuator box | PR #109 | Inclusive `[-0.1,0.1]^3`; the Clarabel QP contains CBF half-spaces only (`cbf/cbf_utils.py:41-123,178-197`), so C0 must be post-QP and reject, never clip. |
| map object | `run.py:52,79`; `splat/gsplat_utils.py:13-83` | Stonehenge `GSplatLoader` is available as an immutable dependency with content identity supplied by `AuthorityRegistry`. |
| map query | `splat/gsplat_utils.py:103-207` | Existing parameterized point/ellipsoid primitive is reusable only behind V2 authority adapters. |
| dynamics | `dynamics/systems.py:3-25,40-68`; `run.py:147` | Position-first forward-Euler double integrator; additive driver can call it only through `PlantCommitAdapter`. |
| plant entry | `run.py:147` | Exact state-changing expression is currently inline. The additive driver owns its own equivalent single call; original `run.py` remains the reference baseline. |
| legacy outcome labels | `run.py:154-177` | Endpoint-only safety, same-query outcome, timeout-as-success, and solver-failure break are quarantined from V2 outcome evaluation. |

## Certification reuse audit

`SweptSegmentCertifier` is parameterized by dynamics, backend, effective radius and `rho_seg`. The L2/H1 shadow contract hard-loads historical V1 `0.11 m` and therefore cannot be imported as V2 authority. Its mathematical backend may be reused behind a typed V2 adapter injected with PR #108 values (`0.025 m`, G3, `rho_seg=0`). `BackupCertifier`, `TerminalCertifier`, and current/full-query adapters are useful parameterized primitives, but their existing combined ownership and wall-clock semantics require typed V2 wrappers rather than direct supervisor authority. Shadow immutable-copy and append-only logging patterns are reusable; the shadow wrapper itself remains non-authoritative and must not be the active driver.

## Alternative inventory

The current runner creates exactly one successful native CBF-QP proposal per cycle and exposes no sibling candidate collection. Therefore `SOURCE_NATIVE_EXISTING` alternative count is zero. The valid V2 result is `NO_ALTERNATIVE_AVAILABLE`; no candidate may be synthesized.

## Feasibility conclusion

All inputs and primitive calls required by an additive active driver are accessible without editing production source. The design verdict is `PASS_ADDITIVE_DRIVER_FEASIBLE`, with production edit requirement `NONE`.
