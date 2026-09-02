# Report: Freeze Cross-Layer Geometry Authority V2

## Answer-first decision

The unique V2 base-radius authority is G0, the frozen Stonehenge controller radius `0.015 m`. G1 contributes the legitimate pre-existing certification margin `0.01 m` exactly once, so every certification point and segment uses `0.025 m`; the active controller remains `0.015 m`. G2 is the separate segment reserve `rho_seg=0.0 m`. G3 is the unchanged static immutable FULL represented-Gaussian map/query authority.

No V2 consumer has an independent robot footprint. Historical `0.10/0.11 m` remains valid for frozen V1 evidence and is quarantined from V2. Tests are 10/10 and validator is 26/26 PASS. No runtime implementation is authorized.

## Authority trace

| Authority | Frozen value/identity | Evidence | Rule |
|---|---|---|---|
| G0 | `CONTROLLER_GEOMETRY_AUTHORITY`, `0.015 m` | `run.py:47-50,115`; `cbf/cbf_utils.py:11-21,45` | Active controller only; unchanged |
| G1 | `CERTIFICATION_MARGIN_AUTHORITY`, `0.01 m` | PR #106 contract raw SHA `23ba083d...a7f3` | Add once at composition |
| G2 | `SEGMENT_RESERVE_AUTHORITY`, `0.0 m` | segment constructor and frozen backend parameter surfaces | Separate from margin |
| G3 | immutable represented-Gaussian map authority | PR #106 and current query path | Same snapshot/frame/scale/filter/sign |

Canonical formula: `r_cert_eff = r_controller + m_cert = 0.015 + 0.01 = 0.025 m`.

## Consumer closure

- I0a and I0b: canonical point view, G0+G1+G3.
- R0: canonical point view, diagnostic/health role only.
- L1: canonical closed immediate segment, G0+G1+G2+G3.
- L2: canonical H1 segment; the legacy `load_frozen_robot_margin_contract()` is forbidden as V2 authority.
- L3: every backup segment and both terminal point/zero-hold witnesses share one injected canonical authority.
- L5: terminal point and zero-hold share the same canonical authority.
- C0, L4 proposal generation, and supervisor arbitration are non-consumers.

The inventory contains 14 roles: 1 controller, 10 certification consumers, and 3 explicit non-consumers. All resolved certification consumers use `0.025 m` and G3; every segment uses `rho_seg=0.0 m`.

## R0/L1 compatibility

L1 certifies the closed segment `[p_k,p_{k+1}]` under the same geometry as R0. Since `p_k` is an endpoint, L1 PASS implies the current-point predicate at `p_k`. R0 therefore remains a cheap diagnostic, consistent with PR #107, while I0a/I0b stay separate admission boundaries.

## Reuse and V1 boundary

The parameterized segment certifier, current adapter, frozen backend adapter, backup certifier, and terminal certifier are reusable only behind typed V2 authority injection. Historical loaders/builders remain replay-only. Missing authority or identity mismatch is `UNKNOWN/BLOCK`; there is no `0.10/0.11` fallback.

V1 is not corrected or reinterpreted. Its `0.11 m`, 14,122 L0 FAIL observations, Case C, and prior shadow evidence remain `HISTORICAL_VALID_UNDER_FROZEN_V1_CONTRACT`.

## Validation and boundary

- Design commit: `72f14b5a53f7a834bae33c39ebc0077b70bb0dd9`.
- Canonical contract raw SHA-256: `36cdd8114e0100da243b8a1786452b1a2bfd5297138bd6dfcd661bbc7803082e`.
- Synthetic tests: 10/10 PASS, including all required legacy/mixed/double-inflation/fallback failures.
- Validator: `PASS_CROSS_LAYER_GEOMETRY_AUTHORITY_V2_VALIDATION`, 26/26.
- Reviewer: `PASS_CROSS_LAYER_GEOMETRY_AUTHORITY_FROZEN`.
- Production/runtime, PR #106, PR #107 logic, and V1 diffs: 0.
- Runtime implementation, rollout, and GPU execution counts: 0.

## Blocker DAG

`CROSS_LAYER_GEOMETRY_AUTHORITY=RESOLVED`. Remaining unresolved blockers are selected-control actuator authority, deadline authority, alternative source, terminal/emergency policy, backup-token runtime schema, and independent evaluation oracle.

`FINAL_STATUS=PASS_CROSS_LAYER_GEOMETRY_AUTHORITY_V2_FREEZE`

`FINAL_DECISION=FREEZE_CROSS_LAYER_GEOMETRY_AND_ADVANCE_BLOCKER_DAG`

Only next task: `FREEZE_SELECTED_CONTROL_ACTUATOR_AUTHORITY_V2`.
