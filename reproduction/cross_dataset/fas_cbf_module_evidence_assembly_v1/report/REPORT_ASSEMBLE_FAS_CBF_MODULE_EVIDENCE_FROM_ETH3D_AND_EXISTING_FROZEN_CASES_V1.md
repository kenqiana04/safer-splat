# ASSEMBLE_FAS_CBF_MODULE_EVIDENCE_FROM_ETH3D_AND_EXISTING_FROZEN_CASES_V1

## Outcome

`PASS_MODULE_WISE_EVIDENCE_WITHOUT_FULL_STACK_SUPERIORITY`

This package integrates 18 frozen compact evidence sources. It runs no new map training, scenario search, controller rollout, tuning, or dataset switch. It preserves PR #81 Case D: ETH3D provides learned-map viability and a structural activation limit, not a DT-invalidity result.

## Evidence roles

- **Official SAFER-map cases:** configuration-specific active module evidence for Start-Safe, Risk-Aware efficiency, DT risk detection, and Predictive Recovery.
- **Replica GT-derived Gaussian map:** clean shared-route controller benchmark; all 99 map-admissible routes succeeded for all methods with zero official-mesh collisions, so outcome saturation prevents superiority inference.
- **ETH3D learned 3DGS:** one external learned map passed minimum controller viability, but its frozen state set contains zero strict endpoint-unsafe/QP-feasible H3 cases after 200000 shadow tuples; no V2 registry, smoke, or formal rollout was permitted.
- **TUM learned-SLAM case study:** shadow precursor and bounded strict-trigger intervention evidence using a GSplat-overlap proxy, not official mesh collision.

## Claim audit

- Configuration-specific claims: C1, C2, C3, C4, C6, C8.
- Partially supported architecture framing: C10, C11.
- Prohibited stronger claims: C5, C7, C9, C12.

Full FAS-CBF superiority over SAFER is **not established**. The paper should be framed as a modular safety-assurance architecture supported by complementary, configuration-bounded evidence rather than a global superiority benchmark.

## Positive, negative, and structural evidence

- Positive: E05_STARTGUARD_FLIGHT100, E06_ACTIVE_PROJECTION, E07_SYNTHETIC_START_STRESS, E08_RISK_AWARE_STONEHENGE, E09_RISK_AWARE_FLIGHT, E11_DT_DETECTION, E13_V4C_H3, E14_V4C_TUNED_H2, E15_HCE_HELDOUT, E17_TUM_DT_FORENSICS, E18_TUM_V4C_INTERVENTION.
- Negative ablations: E04_STARTGUARD_TRIAL57, E10_FORCED_DOMINANCE, E12_V4B_NEGATIVE, E16_TRIAL20_BOUNDARY.
- Structural boundaries: E01_ETH3D_PR80, E02_ETH3D_PR81, E03_REPLICA_PR65.

## Paper architecture

E1 separates map roles; E2 reports Start-Safe with original/post-repair separation; E3 reports constraint/efficiency only within compatible configurations; E4 presents DT detection, precursor, and one-step negative evidence; E5 presents predictive recovery, HCE, and exhaustion; E6 reports Replica saturation and ETH3D learned-map activation limits without a superiority claim.

## Decision

- FINAL_STATUS: `PASS_MODULE_WISE_EVIDENCE_WITHOUT_FULL_STACK_SUPERIORITY`
- FINAL_DECISION: `FRAME_PAPER_AS_MODULAR_SAFETY_ASSURANCE_NOT_GLOBAL_SUPERIORITY`
- Only next task: `INTEGRATE_FAS_CBF_FULL_FRAMEWORK_WITH_MODULE_SPECIFIC_CLAIMS_V1`
