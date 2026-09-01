# Summary

Freezes a design-only V2 L0/controller geometry contract after PR #105 diagnosed `SS-F5 — L0_CONTROLLER_GEOMETRY_CONTRACT_MISMATCH`.

## Frozen upstream

- PR #105: Open Draft
- branch: `diagnose-l0-start-safe-failure-semantics-v1`
- exact head: `3c2ad6122d61436c845cb449c41fae0cd2c1608f`
- base head: `14c844adeda8a0e8eb418abcdbaac62c701e2910`
- V1 remains: 14,122 rows, L0 PASS/FAIL/UNKNOWN `0/14122/0`, Case C

## V2 decision

The controller base footprint and certification margin are now separate authorities:

- `BASE_RADIUS_AUTHORITY = CONTROLLER_GEOMETRY_AUTHORITY`
- Stonehenge `r_controller = 0.015 m`
- `MARGIN_POLICY = PRESERVE_PREEXISTING_CERTIFICATION_MARGIN`
- `m_cert = 0.01 m`
- `r_L0_eff = r_controller + m_cert = 0.025 m`
- `h_L0(p)=min_i[phi_i*d_i^2-r_L0_eff^2]`

The controller authority chain is `run.py` Stonehenge `radius` → `CBF.radius` → shared Gaussian `query_distance(radius=...)`. Future L0 code must consume the authority read-only and must not duplicate `0.015` as a second hard-coded value.

The margin predates the diagnosis: commit `04ebca2b1b35124ad0e61ebed96e491c9edae4bb` separately named `FIXED_SAFETY_MARGIN_M=0.01` and composed it additively. Its preservation is not sentinel- or outcome-driven.

Canonical contract SHA-256: `23ba083d871d17f6389dde2872068e7439cba6898197572fc34246b5b46da7f3`.

## Unchanged from V1

- query state `state[:3]`
- frame, axis, and scale conventions
- one Gaussian log-scale exponentiation
- map/checkpoint identity and FULL Gaussian set
- opacity/filter behavior
- point-to-ellipsoid math and min aggregation
- PASS/FAIL/UNKNOWN sign semantics
- no candidate dependence in L0
- L1/L2 formulas
- worker-side shadow gating
- controller runtime and committed action

## Evidence boundary

V1's `0.11` contract remains internally consistent and historically immutable. V2 is a new geometry contract, not corrected V1 results. The 15 sentinels are retained only as root-cause evidence and a future conformance fixture; they did not select any V2 parameter.

## Future verification order

1. V2-A static single-authority implementation validation.
2. V2-B frozen 15-point contract conformance without parameter changes.
3. V2-C shadow OFF-vs-ON controller noninterference.
4. V2-D support-only pilot exposing only L0 PASS/non-PASS and L1/L2 reached counts; L2 status distribution remains hidden.
5. V2-E eligibility to design a separate formal cohort protocol only after support is established.

No stage is executed in this PR.

## Validation and decision

- 5 contract tests
- `PASS_L0_CONTROLLER_GEOMETRY_CONTRACT_V2_DESIGN_VALIDATION`
- reviewer: `PASS_READY_FOR_SHADOW_IMPLEMENTATION_ONLY`
- `FINAL_STATUS=PASS_L0_CONTROLLER_GEOMETRY_CONTRACT_V2_DESIGN`
- `FINAL_DECISION=FREEZE_V2_GEOMETRY_CONTRACT_AND_AUTHORIZE_SHADOW_IMPLEMENTATION`
- only next task: `IMPLEMENT_L0_CONTROLLER_GEOMETRY_CONTRACT_V2`

This PR makes no safety, performance, reachability-improvement, or L2-support claim.
