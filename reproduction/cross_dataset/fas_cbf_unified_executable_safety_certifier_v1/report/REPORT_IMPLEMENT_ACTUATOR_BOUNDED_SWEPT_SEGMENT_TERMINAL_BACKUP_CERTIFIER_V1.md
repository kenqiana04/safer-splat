# Report: Actuator-Bounded Swept-Segment Terminal-Backup Certifier V1

## Outcome

`PASS_GAUSSIAN_MAP_UNIFIED_EXECUTABLE_SAFETY_CERTIFIER_V1`

`FREEZE_CERTIFIER_AND_BUILD_MINIMAL_ACTIVATED_REPLICA_GT_BENCHMARK`

Only next task: `BUILD_REPLICA_GT_EXECUTABLE_SAFETY_ACTIVATED_BENCHMARK_V1`.

This task implements a candidate-level executable-safety certifier. It does not train or mutate a map, run a navigation rollout, enumerate continuous `U_exec`, establish deployment safety or global recursive feasibility, or compare full-stack performance against SAFER.

## Required closeout

1. **Branch:** `fas-cbf-unified-executable-safety-certifier-v1`.
2. **Draft PR:** to be created against `fas-cbf-core-v1-conceptual-closure` after final validation.
3. **Commit:** `feat(reproduction): implement unified executable safety certifier v1` after final validation.
4. **Base/head:** frozen base `17805e67b75412dc21b1a5fff4143ea3bc985f7f`; result head recorded after commit.
5. **PR #83 preserved:** state `OPEN`, draft `True`, mergeable `MERGEABLE`; no rewrite or mutation.
6. **Frozen identities:** 10 canonical Git-blob artifacts and 9 protected sources.
7. **Normative model:** `POSITION_FIRST_FORWARD_EULER_DOUBLE_INTEGRATOR_V1`.
8. **Model consistency:** plant, V4-B verifier/plant and V4-C backup/plant all use `x_next=x+dt*[v,u]`; audit `PASS_NORMATIVE_MODEL_CONSISTENCY`.
9. **Actuator bounds:** `u in [-0.1,0.1]^3`, `v in [-0.1,0.1]^3`, `dt=0.05`; bounds inclusive, no hidden clipping.
10. **Barrier semantics:** Gaussian represented-obstacle barrier proxy with total footprint/margin `0.11 m`; it is not labelled metric clearance or reference truth.
11. **Gaussian segment backend:** exact analytic line-segment minimum for isotropic primitives plus a general signed-distance interval backend.
12. **Classification:** `EXACT_ANALYTIC`, `CONSERVATIVE_LOWER_BOUND`, and separate `DIAGNOSTIC_ONLY`; endpoint fallback is disabled.
13. **Synthetic segment tests:** 15 preregistered cases include interior collision, tangent, UNKNOWN and snapshot change.
14. **Randomized segment tests:** 10000 total, including 1000 conservative-bound cross-checks at seed 20260805.
15. **False-safe:** 0; false rejects 0; inconclusive 0.
16. **Terminal set:** `BRAKING_TO_REST_TERMINAL_SET_V1`, sufficient under static-map/no-error assumptions, not maximal.
17. **Terminal tolerance:** `1e-12` m/s, derived as rounded-up 4096 float64 ulps at unit scale before tests.
18. **Braking policy:** componentwise non-reversing `clip(-v/dt,u_min,u_max)` without reference or goal input.
19. **H_stop:** `max_i ceil(|v_i|/(a_brake,i*dt))`; global frozen-budget bound is 20 steps, followed by one zero hold.
20. **Backup witness:** candidate immediate segment, every bounded braking segment, terminal state and zero-hold segment are retained in-memory; Git stores compact evidence only.
21. **Tail-witness:** R1 holds only for an unchanged snapshot, exact predicted state/model and no delay, disturbance or tracking error.
22. **Unified certifier:** commits only after actuator, current full query/optional full CBF rows, swept segment and backup all pass.
23. **Typed statuses:** all 13 authorized outputs are represented and every state-machine path returns to next-cycle diagnosis.
24. **Candidate library:** nominal, existing-filtered, deterministic task-local alternatives and deterministic braking, ordered by frozen provenance/ID.
25. **Exhaustion semantics:** `FAIL_CLOSED_BACKUP_WITNESS_NOT_FOUND_IN_FROZEN_LIBRARY`; never mathematical unrecoverability.
26. **State machine:** exhaustive path validation passes; terminal zero hold returns `NEXT_CYCLE_DIAGNOSIS`.
27. **Replica smoke:** `PASS_REPLICA_GT_FINE_PLANT_FREE_MAP_SMOKE`, 25 plant-free states, exact sphere backend, 2285656 primitives. Statuses: {'CERTIFIED_TERMINAL_ACTION': 10, 'CERTIFIED_NOMINAL_CONTROL': 10, 'FAIL_CLOSED_CURRENT_CBF_INFEASIBLE': 5}. The requested backup-not-found class was structurally absent and was not manufactured.
28. **ETH3D compatibility:** optional, not executed; expected frozen map SHA remains `927734a2339a3f2710640065b0893eaae162cc0144ac67e2f377bcff2e71ae34` and mutation count is zero.
29. **Reference online access:** 0. Offline mesh evaluation was not required for the compatibility smoke.
30. **Timing:** retained by component and typed outcome in `timing_by_outcome.json`; no real-time threshold or claim was introduced.
31. **Proof status:** S1/B1/R1/F1 are `PROVED_UNDER_EXPLICIT_ASSUMPTIONS` with `TESTED_IMPLEMENTATION_CONSISTENCY`.
32. **Unresolved proofs:** map-to-world truth, delay/disturbance/tracking robustness, search completeness, global recursive feasibility, maximal terminality and deployment safety.
33. **Map operations:** training 0, mutation 0, dataset switch 0.
34. **Tuning:** controller parameter 0, safety threshold 0.
35. **Protected source:** mutation count 0.
36. **GPU final:** ['1, NVIDIA GeForce RTX 4090, 6 MiB, 0 %']; compute process count 0; task process count 0.
37. **Watchdog/SSH:** watchdog `Running`, loopback proxy listener True; SSH/network/firewall restarts all zero.
38. **Operational autonomy:** 5 recorded actions; task-owned cleanup count 1.
39. **Validator:** `PASS_UNIFIED_EXECUTABLE_SAFETY_CERTIFIER_VALIDATION`; syntax compile exit 0 across 66 files; pytest 33 passed.
40. **FINAL_STATUS:** `PASS_GAUSSIAN_MAP_UNIFIED_EXECUTABLE_SAFETY_CERTIFIER_V1`.
41. **FINAL_DECISION:** `FREEZE_CERTIFIER_AND_BUILD_MINIMAL_ACTIVATED_REPLICA_GT_BENCHMARK`.
42. **Unresolved evidence:** no real robot, delayed/noisy plant, complete candidate search, maximal terminal set, learned-map deployment or full-stack paired benchmark evidence.
43. **Server report:** `/disk1/zlab/maintenance_records/fas_cbf_unified_executable_safety_certifier_v1/report/REPORT_IMPLEMENT_ACTUATOR_BOUNDED_SWEPT_SEGMENT_TERMINAL_BACKUP_CERTIFIER_V1.md`.
44. **Downstream handoff:** `report/downstream_handoff.json`.
45. **Only next task:** `BUILD_REPLICA_GT_EXECUTABLE_SAFETY_ACTIVATED_BENCHMARK_V1`.

## Claim-evidence map

| Claim | Evidence | Status |
| --- | --- | --- |
| Candidate-level four-gate certifier is implemented | typed implementation and 33 passing tests | supported |
| Continuous represented-map interval is checked | exact sphere derivation, conservative signed-distance bound, 10000 randomized cases | supported under assumptions |
| Braking-to-rest witness is finite under authority | derivation and 2000/2000 property cases | supported under assumptions |
| Frozen map adapter is compatible | 25 plant-free Replica states, reference online reads 0 | compatibility only |
| Global recursive feasibility or deployment safety | no such evidence collected | explicitly unsupported |

## Adversarial self-review

- **Contribution:** executable candidate-level closure is implemented; continuous-space completeness is not claimed.
- **Clarity:** normative model, typed outputs, exact/conservative/diagnostic roles and failure semantics are explicit.
- **Experimental strength:** synthetic/property tests and bounded smoke test implementation consistency, not superiority.
- **Evaluation completeness:** delayed/noisy plant, full-stack paired comparison and learned-map deployment remain future evidence.
- **Method soundness:** UNKNOWN, nonfinite, budget exhaustion, snapshot change and absent witness all fail closed without being relabelled unrecoverable.
