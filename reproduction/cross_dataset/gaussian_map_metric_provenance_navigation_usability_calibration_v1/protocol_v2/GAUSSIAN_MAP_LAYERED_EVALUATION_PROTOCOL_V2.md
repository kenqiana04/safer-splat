# Gaussian Map Layered Evaluation Protocol V2

## 1. Scope and terminology

This protocol evaluates immutable Gaussian-map instances for three separate claims: global reconstruction evidence, limited-domain navigation evidence, and safety-query compatibility. A renderer's accepted set is `K_tau`; its complement is UNKNOWN, not FREE.

## 2. Provenance requirements

Every formula records one allowed formula-source enum. Every numerical decision point records one allowed threshold-source enum, applicability domain, first task/commit, rationale, decision role, failure implication, and non-implication. `PROJECT_HEURISTIC` and `UNDOCUMENTED_OR_UNRESOLVED` cannot be universal navigation gates.

## 3. Integrity hard gates

Identity, TRAIN/HELDOUT non-leakage, metric units/pose/intrinsics, finite required outputs, deterministic canonical export, query immutability, exact numerical engine qualification, independent-oracle identity, and absence of unauthorized post-processing are hard gates. Integrity failure yields `R0_INVALID` and stops qualification, but diagnostic evidence required for attribution may still be produced read-only.

## 4. Descriptive reconstruction evaluation

Report native and common semantics without favorable selection. At the fixed alpha grid `{0.05,0.10,0.20,0.30,0.40,0.50,0.60,0.70,0.80,0.90,0.95}`, report global/frame/group/worst-5% coverage and accepted-support AbsRel, RMSE, SqRel, delta1/2/3, median ratio, nonfinite, accepted and rejected counts. AURC is trapezoidal conditional risk over the observed coverage interval and is descriptive only. Missing grid evidence is `NOT_EVALUABLE`, never interpolated.

Where independent metric geometry and immutable samples exist, report accuracy, completeness, F-score, boundary recall, false-positive rate, and thin-structure recall at `{0.01,0.02,0.03,0.05,0.10,0.20}` metres. These are reporting coordinates, not pass cutoffs. Aggregate globally, frame macro, group macro, worst 5%, worst spatial component, range, border, and robot-height band when supported.

## 5. Missing geometry and unknown policy

Measure connected 2D missing components, back-projected 3D clustering, persistence, range/border/robot-height distributions, and route-tube intersection only when the retained evidence supports them. Held-out rays certify only their observable domain. UNKNOWN must be excluded or assigned an explicitly frozen conservative/high-cost policy; it is never silently free.

## 6. One-sided safety risk and physical budget

Use `e_plus=max(0,d_map-d_ref)`. For a frozen robot and route, `m_ref=d_ref-r_robot` and `B_map_available=m_ref-epsilon_loc-epsilon_shape-epsilon_sampled-epsilon_stop-epsilon_tracking`. A necessary route condition is `UpperBound[e_plus | swept route tube] <= B_map_available`. Label the bound as exact, deterministic frozen-sample maximum, bootstrap UCB, conformal, or empirical percentile. A p99 is never called a certificate. Any missing allowance source yields `PHYSICAL_ERROR_BUDGET_UNRESOLVED`.

## 7. Physical navigation hard gates

UNKNOWN is not FREE; the reference swept body has no obstacle collision; the route-tube overestimation upper bound is within the physical budget; velocity/actuation/dynamics contracts hold; and an independent collision predicate passes. Global coverage, alpha, AbsRel, delta1, ratio, PSNR, SSIM, LPIPS, Gaussian count, single runtime and AURC cannot alone be universal navigation gates.

## 8. Two-axis classification

Reconstruction: `R0_INVALID`, `R1_DIAGNOSTIC_RECONSTRUCTION`, `R2_GLOBAL_RECONSTRUCTION_CANDIDATE`, `R3_GLOBAL_DENSE_RECONSTRUCTION_QUALIFIED`. R3 requires independent multi-scene or benchmark calibration.

Navigation: `N0_NOT_EVALUABLE`, `N1_NAVIGATION_DIAGNOSTIC_ONLY`, `N2_LIMITED_DOMAIN_UNKNOWN_AWARE_NAVIGATION_CANDIDATE`, `N3_LIMITED_DOMAIN_NAVIGATION_QUALIFIED`. N3 requires complete route-tube, physical-budget and independent-oracle evidence. `SAFETY_QUERY_COMPATIBLE` is recorded separately.

## 9. Reference authority and uncertainty

Authority A is independent metric geometry; B is independent observable rays; C is interface or unresolved evidence. Full-space claims require A. Formal method claims freeze seed count before training. Single seed supports only the map instance. Confidence intervals cluster by frame, group, route or map—not pixels—and report spatial autocorrelation, worst components, map variance and domain shift.

## 10. Artifact, early-stop and claims

Freeze map/checkpoint/canonical SHA, source commit, renderer, reference and route identities before evaluation and verify immutability after. Early-stop may close formal PASS but must not suppress read-only attribution diagnostics. Never repair scale, ICP/Sim3-align, filter opacity, delete frames or choose a favorable threshold/channel without a separate preregistered task. Preserve every legacy result verbatim and label V2 outputs provisional until the retrospective requalification task.

## 11. Requalification and new-dataset entry

Run controls before candidates. Candidates cannot fit their own gate. If control evidence is insufficient, record `NO_UNIVERSAL_NUMERIC_GATE_JUSTIFIED_BY_CURRENT_EVIDENCE`. Requalification produces two axes and bounded claims, not a rewritten historical PR. A new dataset must pass the separate entry checklist before formal training.
