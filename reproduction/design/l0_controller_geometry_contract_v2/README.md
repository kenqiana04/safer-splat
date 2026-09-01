# L0/Controller Geometry Contract V2 — Design Only

This package freezes a new shadow L0 geometry contract after PR #105 diagnosed `SS-F5 — L0_CONTROLLER_GEOMETRY_CONTRACT_MISMATCH`.

The V2 decision is intentionally narrow:

- base footprint authority: the frozen controller's operational geometry authority;
- Stonehenge controller radius: `0.015 m` from `run.py` → `CBF.radius` → Gaussian query;
- preserved pre-existing certification margin: `0.01 m` from `FIXED_SAFETY_MARGIN_M`;
- effective L0 radius: `0.025 m`;
- composition: `r_L0_eff = r_controller + m_cert` exactly once.

The contract does not change the controller, map, Gaussian set, opacity/filter behavior, frame, scale, state reference, barrier formula, status sign, L1/L2, or shadow gating. It does not run a sentinel query, pilot, rollout, or formal cohort.

V1 remains frozen at `0 / 14,122 / 0` L0 PASS/FAIL/UNKNOWN and Case C. V2 is a new design, not corrected V1 evidence.

Canonical contract SHA-256: `23ba083d871d17f6389dde2872068e7439cba6898197572fc34246b5b46da7f3`.
