# REPORT: Validate L2/H1 Shadow Certifier on Frozen Replay V1

## Direct answers

1. **Q1 — Frozen source universe.** PR #89 normalized one-step candidates, non-duplicated PR #87 activated one-step candidates, genuinely logged B3 alternatives, and PR #87 rollout-step evidence. It was frozen before L2 results: **YES**.
2. **Q2 — N_all.** **6853** candidate/state/map-relevant historical rows under the predeclared construction rule.
3. **Q3 — Replayability.** FORMAL_REPLAYABLE=2594; DIAGNOSTIC_RECONSTRUCTABLE=0; NOT_REPLAYABLE=4259.
4. **Q4 — Main non-replayability.** MISSING_U_K=4259; overlapping MISSING_CANDIDATE_IDENTITY=792.
5. **Q5 — Evidence-reached L2.** **788**.
6. **Q6 — Architecture-eligible formal replay.** **788** unique candidates.
7. **Q7 — L2 outcomes.** PASS=770, FAIL=18, UNKNOWN=0; denominator=788.
8. **Q8 — UNKNOWN causes.** None observed; N_L2_UNKNOWN=0.
9. **Q9 — Was NOT_REPLAYABLE counted as UNKNOWN?** **NO**.
10. **Q10 — Stored L1 paired analysis.** **YES for all 788 primary rows**; all carry stored historical L1 PASS.
11. **Q11 — N_L1_PASS_L2_FAIL.** **18**.
12. **Q12 — Collision prevented?** **NO**. This is offline information increment only.
13. **Q13 — Multi-candidate disagreement.** 20 historical groups had multiple candidates and distinct H1 endpoints; formal status disagreement=0.
14. **Q14 — Any new candidate?** **NO**.
15. **Q15 — Source/missingness bias?** **YES**. Missing numeric rollout controls and source-specific reachability strongly select the replayable/primary subset.
16. **Q16 — Deterministic?** **YES**, two final complete passes have identical semantic hashes and zero row mismatches.
17. **Q17 — Fidelity mismatch?** **NO**, 16 preselected direct-backend checks all match endpoint, status, reason, value, and candidate hash.
18. **Q18 — Controller/shadow/map/dynamics modified?** **NO**. Only task-local import/lineage wrapper corrections were made.
19. **Q19 — On-policy/navigation experiment run?** **NO**.
20. **Q20 — Strongest supported claim.** On this frozen, architecture-reached cohort, PR #94 deterministically adds 18 candidate-dependent L2 future-safety FAIL signals after stored L1 PASS.
21. **Q21 — Unsupported claims.** Collision prevention, closed-loop improvement, controller efficacy, runtime performance, recursive feasibility, physical-world safety, or deployment readiness.
22. **Q22 — Next phase.** Design non-invasive on-policy shadow observation; do not grant controller authority.

## Denominators and mechanism result

Replay coverage is 2594/6853 (37.852036%). Primary opportunity coverage is 788/788. L1 PASS/L2 FAIL prevalence is 18/788 (2.284264%); L1 PASS/L2 UNKNOWN is 0/788. These are descriptive mechanism signals only.

## Candidate strata and multi-candidate evidence

Executed/selected candidates and logged non-executed candidates are reported separately. The latter never receive historical closed-loop counterfactual authority. The 20 legitimate multi-candidate groups all have distinct H1 endpoints but no PASS/FAIL/UNKNOWN disagreement.

## Reproducibility and repair disclosure

The first server attempt stopped before evaluation because a task-local dynamically loaded dataclass module was not registered in `sys.modules`; this wrapper was fixed without scientific mutation. One complete result pass then exposed a task-local lineage merge-order issue (`l2_reached` was overwritten by the shadow result's null metadata); pre-fix outputs were preserved on the server, the merge order was corrected, and the same frozen replay was repeated. The final two full passes are deterministic and direct-backend differential checks pass. No controller, PR #94 implementation, map, dynamics, threshold, candidate, or protected blob changed.

## Decision

`CASE_A — VALID_INTERPRETABLE_FROZEN_REPLAY`

- FINAL_STATUS: `PASS_L2_H1_FROZEN_REPLAY_VALIDATION_V1`
- FINAL_DECISION: `FREEZE_REPLAY_EVIDENCE_AND_PREPARE_NONINVASIVE_ON_POLICY_SHADOW_OBSERVATION`
- Only next task: `DESIGN_L2_H1_ON_POLICY_SHADOW_OBSERVATION_V1`
