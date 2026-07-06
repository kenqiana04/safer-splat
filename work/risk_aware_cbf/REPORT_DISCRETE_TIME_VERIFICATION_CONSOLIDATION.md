# Discrete-Time Verification Consolidation for FAS-CBF

## 1. Purpose

This report consolidates Discrete-Time Verification as an independent core module of FAS-CBF. The goal is not to introduce another recovery method; it is to make the sampled-data verification layer explicit and separate from optional predictive recovery.

## 2. Methodology Context

The consolidated framework is:

Certified Feasibility-Aware Start-Safe CBF + Discrete-Time Verification + optional Predictive Recovery.

The start-safe CBF layer handles initial feasibility and safe-start projection. DT Verification audits sampled-data margin risk under the discrete dynamics. Optional Predictive Recovery is triggered only when DT Verification reports warning/on-margin risk.

## 3. Existing Evidence Inventory

The inventory is stored at `work/risk_aware_cbf/results/dt_verification_consolidation/existing_dt_evidence_inventory.csv` and `.md`. It indexes V4-A, V4-B, V4-C, tuned R4, and synthetic post-repair evidence without treating predictive recovery as the verification layer itself.

## 4. Verification-Only Audit

The verification-only audit reads the saved V4-A + V1 dense-flight trajectory and performs H=1/H=2/H=3 repeated-control rollout checks. No V4-C recovery is executed. In this audit, base rollout and executed rollout are identical.

| horizon | num_trials | num_steps | margin_violation_count | min_horizon_h_min | collision_count | qp_infeasible_count |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | 100 | 14422 | 463 | 0.000197846 | 0 | 0 |
| 2 | 100 | 14422 | 488 | 0.000197208 | 0 | 0 |
| 3 | 100 | 14422 | 519 | 0.000195183 | 0 | 0 |

## 5. Horizon Ablation

H=1 checks immediate one-step sampled-data risk. H=2 is the practical trigger horizon supporting R4_H2_N64. H=3 is the robust reference horizon.

- H=1 margin violations: 463
- H=2 margin violations: 488
- H=3 margin violations: 519

## 6. H2-H3 Overlap

| level | H2_count | H3_count | H2_only | H3_only | H2_and_H3 | H2_coverage_of_H3 | H3_extra_over_H2 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| step | 488 | 519 | 0 | 31 | 488 | 0.94027 | 31 |
| trial | 19 | 23 | 0 | 4 | 19 | 0.826087 | 4 |

H=2 is sufficient to support the tested dense-flight R4_H2_N64 practical configuration because R4_H2_N64 achieves zero executed H-step margin violations in full100 while substantially reducing runtime. H=3 should remain the robust reference because it detects a superset or near-superset of risks and provides a more conservative audit horizon.

## 7. Margin Violation vs Collision

Margin violation is not collision. V4-A + V1 can be collision-free while still having sampled-data margin risks. In the consolidated evidence, the V4-A + V1 navigation has collision_count=0 and qp_infeasible_count=0, while the verification-only audit detects nonzero H-step margin violations.

## 8. Decision Rule

Normal execution means the H-step minimum safety value is at or above `dt_margin`. Warning/on-margin means the H-step minimum safety value falls below `dt_margin`. Optional predictive recovery is triggered only on warning/on-margin risk. If recovery fails or the executed H-step rollout remains below margin, the risk remains unresolved and must be reported separately from collision.

## 9. Relationship to Optional Predictive Recovery

V4-C is an optional triggered recovery response to DT Verification. It is not the primary controller and not an always-on default. H3_N128 is retained as a robust reference. R4_H2_N64 is the dense-flight practical tuned configuration.

| run | collision_count | qp_infeasible_count | horizon | base_horizon_margin_violation_count | exec_horizon_margin_violation_count | predictive_recovery_success_count | recovery_failed_count | runtime_mean | runtime_p95 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| V4-A active projection + V1 verification-only H1 | 0 | 0 | 1 | 463 | 463 |  |  |  |  |
| V4-A active projection + V1 verification-only H2 | 0 | 0 | 2 | 488 | 488 |  |  |  |  |
| V4-A active projection + V1 verification-only H3 | 0 | 0 | 3 | 519 | 519 |  |  |  |  |
| V4-A active projection + V1 flight100 | 0 | 0 | NA |  |  |  |  | 0.0575582 | 0.0643087 |
| V4-C H3_N128 full100 | 0 | 0 | 3 | 236 | 0 | 236 | 0 | 0.170388 | 0.702523 |
| V4-C R4_H2_N64 full100 | 0 | 0 | 2 | 193 | 0 | 193 | 0 | 0.0959517 | 0.309428 |

The verification-only rows and V4-C rows use different trajectory contexts. Verification-only counts are computed on the saved V4-A + V1 no-recovery trajectory. V4-C base counts are computed inside recovery-enabled runs after prior triggered recovery decisions may already have changed the later trajectory. They should therefore be used for complementary evidence, not treated as identical counters.

## 10. Methodology Completion Check

The dense-flight methodology is closed enough to enter method and experiment writing: start-safe feasibility handling is separated from post-repair navigation, DT Verification is consolidated as an independent module, and optional predictive recovery is framed as triggered response rather than the main method.

## 11. Limitations

No new CBF theorem is claimed. `min_safety_h` is the repository GSplat ellipsoid safety h value, not meter clearance. Synthetic starts are not official benchmark starts. Post-repair navigation is not original benchmark navigation. The official SAFER-Splat baseline source is not modified. Margin violations and collisions are reported separately.
