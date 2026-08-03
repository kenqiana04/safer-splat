# REPORT: Retrospective Requalification of Existing Gaussian Maps under Layered Protocol V2

## Executive result

**NO_EXISTING_LEARNED_GAUSSIAN_MAP_NAVIGATION_QUALIFIED_UNDER_PROTOCOL_V2**

Frozen decision-tree outcome: **PROCEED_TO_NEW_DATASET_ENTRY_QUALIFICATION**. The only next task is **ETH3D_DELIVERY_AREA_PROTOCOL_V2_ENTRY_QUALIFICATION_V1**, which authorizes entry qualification only—not ETH3D download or training.

Protocol V2 correctly discriminated the controls. The GT-derived positive control reached R3/N3, while the executable learned negative control remained R1/N1 despite finite G0 queries. No learned map reached N2 or N3. Six existing artifacts were inspected read-only; five unavailable artifacts were retained as unavailable rather than reconstructed.

## Frozen identities and scope

- Upstream PR/head: #75 at `d1d3301076bec33868c52ff49e81857379038de1`; base branch `gaussian-map-metric-provenance-navigation-usability-calibration-v1`.
- Protocol V2 SHA-256: `a0a02fd284c75c600095510899e2878f198d69ff088b66eccd3313275fdbde7e`.
- New-dataset checklist SHA-256: `7c95f787fd7fb503e4bd2726546debac53acd41c1d5f9a8dd08c29cb27735593`.
- PR #75 report SHA-256: `9b0743571d6df1e4d4063c7d114a7ebb99d8a4092c4cdbda9384720e121d1678`.
- Identity method: raw Git blob bytes from the frozen upstream head; working-tree EOL conversion is excluded.
- This task performed no download, training, optimization, resume, map mutation, filtering, registration, scale repair, frame deletion, controller run, planner run, or route generation.
- For every entry, the legacy result remains valid under legacy contract. Historical PR #68–#75 conclusions remain valid under their original contracts. V2 supplies a new task-specific classification and does not rewrite history.

## Map inventory and Protocol V2 classification

Inventory: 11 fixed entries; 6 accessible and 5 unavailable for retrospective execution.

| Map | Artifact | Learned | R axis | N axis | Query | Reference | Unknown | Physical budget |
|---|---:|---:|---|---|---|---|---|---|
| REPLICA_GT_FINE | available | false | R3_GLOBAL_DENSE_RECONSTRUCTION_QUALIFIED | N3_LIMITED_DOMAIN_NAVIGATION_QUALIFIED | true | A_DENSE_INDEPENDENT_GEOMETRY | NOT_APPLICABLE_GT_DERIVED_FULL_REFERENCE | PHYSICAL_ERROR_BUDGET_RESOLVED |
| REPLICA_SPLATFACTO | available | true | R1_DIAGNOSTIC_RECONSTRUCTION | N1_NAVIGATION_DIAGNOSTIC_ONLY | true | A_DENSE_INDEPENDENT_GEOMETRY | UNKNOWN_MODEL_UNRESOLVED | PHYSICAL_ERROR_BUDGET_UNRESOLVED |
| TUM_SPLATFACTO_NEGATIVE | unavailable | true | R1_DIAGNOSTIC_RECONSTRUCTION | N0_NOT_EVALUABLE | NOT_EVALUABLE | B_OBSERVABLE_RAY_REFERENCE | UNKNOWN_MODEL_UNRESOLVED | PHYSICAL_ERROR_BUDGET_UNRESOLVED |
| REPLICA_SPLATAM_60 | available | true | R1_DIAGNOSTIC_RECONSTRUCTION | N1_NAVIGATION_DIAGNOSTIC_ONLY | true | A_DENSE_INDEPENDENT_GEOMETRY | UNKNOWN_MODEL_UNRESOLVED | PHYSICAL_ERROR_BUDGET_UNRESOLVED |
| ARKITSCENES_M1_SPLATAM | available | true | R2_GLOBAL_RECONSTRUCTION_CANDIDATE | N0_NOT_EVALUABLE | true | B_OBSERVABLE_RAY_REFERENCE | UNKNOWN_MODEL_DIAGNOSTIC_ONLY | PHYSICAL_ERROR_BUDGET_UNRESOLVED |
| TUM_SPLATAM_FORMAL | available | true | R1_DIAGNOSTIC_RECONSTRUCTION | N0_NOT_EVALUABLE | true | B_OBSERVABLE_RAY_REFERENCE | UNKNOWN_MODEL_UNRESOLVED | PHYSICAL_ERROR_BUDGET_UNRESOLVED |
| TUM_GAUSSIAN_SLAM | available | true | R1_DIAGNOSTIC_RECONSTRUCTION | N0_NOT_EVALUABLE | true | B_OBSERVABLE_RAY_REFERENCE | UNKNOWN_MODEL_UNRESOLVED | PHYSICAL_ERROR_BUDGET_UNRESOLVED |
| SAFER_OFFICIAL_FLIGHT | unavailable | true | R1_DIAGNOSTIC_RECONSTRUCTION | N0_NOT_EVALUABLE | NOT_EVALUABLE | C_INTERFACE_ONLY | UNKNOWN_MODEL_UNRESOLVED | PHYSICAL_ERROR_BUDGET_UNRESOLVED |
| SAFER_OFFICIAL_OLD_UNION2 | unavailable | true | R1_DIAGNOSTIC_RECONSTRUCTION | N0_NOT_EVALUABLE | NOT_EVALUABLE | C_INTERFACE_ONLY | UNKNOWN_MODEL_UNRESOLVED | PHYSICAL_ERROR_BUDGET_UNRESOLVED |
| SAFER_OFFICIAL_STATUES | unavailable | true | R1_DIAGNOSTIC_RECONSTRUCTION | N0_NOT_EVALUABLE | NOT_EVALUABLE | C_INTERFACE_ONLY | UNKNOWN_MODEL_UNRESOLVED | PHYSICAL_ERROR_BUDGET_UNRESOLVED |
| SAFER_OFFICIAL_STONEHENGE | unavailable | true | R1_DIAGNOSTIC_RECONSTRUCTION | N0_NOT_EVALUABLE | NOT_EVALUABLE | C_INTERFACE_ONLY | UNKNOWN_MODEL_UNRESOLVED | PHYSICAL_ERROR_BUDGET_UNRESOLVED |

The GT-derived map is a control, not a learned-map success. `SAFETY_QUERY_COMPATIBLE=true` is reported independently and never raises either axis.

## Control-first gate

Control discrimination: **PASS_PROTOCOL_V2_CONTROL_DISCRIMINATION**. Positive control: R3_GLOBAL_DENSE_RECONSTRUCTION_QUALIFIED/N3_LIMITED_DOMAIN_NAVIGATION_QUALIFIED, query=true, frozen route/oracle closure retained. Negative control: R1_DIAGNOSTIC_RECONSTRUCTION/N1_NAVIGATION_DIAGNOSTIC_ONLY, query=true; finite G0 did not create a navigation qualification. TUM Splatfacto remains historical negative evidence because its artifact is unavailable.

The initial generic GT G0 wrapper mishandled inactive uniform-sphere entries and a subsequent retry called the CUDA peak-memory reset before CUDA initialization. Both wrapper-only failures are preserved. The wrapper was corrected without modifying map bytes or the SAFER solver, then all three required fresh GT processes passed deterministically.

## Evidence channels

Native/common parity counts: `{'NATIVE_ONLY': 1, 'NOT_EVALUABLE': 5, 'NUMERIC_PARITY_PASS': 2, 'SEMANTIC_PARITY_ONLY': 3}`. TUM SplaTAM and TUM Gaussian-SLAM have numeric parity; three maps have semantic parity only; ARKit M1 is native-only; five artifacts are not evaluable. Renderer selection was not changed to favor a candidate.

Risk–coverage uses the frozen 11-point alpha grid. ARKit M1 reuses one complete frozen curve and its historical alpha=0.5 point; Replica learned maps have only retained single working points; TUM entries have historical single geometry evidence. No interpolation, candidate-specific alpha, rerender, or hard AURC gate was introduced.

Multi-tolerance reporting uses 0.01/0.02/0.03/0.05/0.10/0.20 m. Only the GT-derived deterministic construction certificate is complete; no learned map has retained bidirectional samples sufficient for a full new multi-tolerance curve. Authority-B claims remain observable-ray bounded and are not called full-space completeness.

UNKNOWN is never treated as FREE. ARKit M1 supports diagnostic missingness only; ten other entries are unresolved or not applicable to the GT-derived full-reference control. Diagnostic rejected-pixel or observable-ray masks are not represented as a deployable runtime unknown model.

Only the GT-derived Replica control has a frozen route-coordinate contract, 100-route registry, swept-body oracle, one-sided deterministic certificate, and resolved physical budget. Replica learned maps do not have a proven coordinate identity to that route registry. No candidate-dependent route was generated. The exact one-sided engine was independently checked on 256 frozen queries with chunked full-map evaluation; empirical-only evidence is not promoted to N3.

## Read-only SAFER G0

Six accessible maps ran 256 fixed queries in three fresh processes each (18 total) on physical GPU 1. Every final process produced finite h/gradient/Hessian values, symmetric Hessians, deterministic active indices and unchanged source identity. The source was the corrected world-frame Hessian implementation at commit `f63b4c496861c4f8881348d74244c1ff9a528d51`. G0 establishes query compatibility only.

| Map | Processes | Max runtime (s) | Max peak GPU bytes | Result |
|---|---:|---:|---:|---|
| REPLICA_GT_FINE | 3 | 0.334639 | 359009792 | PASS |
| REPLICA_SPLATFACTO | 3 | 6.358951 | 759052800 | PASS |
| TUM_SPLATFACTO_NEGATIVE | 0 | — | — | NOT_EVALUABLE |
| REPLICA_SPLATAM_60 | 3 | 9.169886 | 1160249856 | PASS |
| ARKITSCENES_M1_SPLATAM | 3 | 30.413129 | 3474152448 | PASS |
| TUM_SPLATAM_FORMAL | 3 | 25.824859 | 2942837248 | PASS |
| TUM_GAUSSIAN_SLAM | 3 | 13.572888 | 1643708928 | PASS |
| SAFER_OFFICIAL_FLIGHT | 0 | — | — | NOT_EVALUABLE |
| SAFER_OFFICIAL_OLD_UNION2 | 0 | — | — | NOT_EVALUABLE |
| SAFER_OFFICIAL_STATUES | 0 | — | — | NOT_EVALUABLE |
| SAFER_OFFICIAL_STONEHENGE | 0 | — | — | NOT_EVALUABLE |

## Candidate-specific conclusions

- **Replica SplaTAM 60:** the legacy delta1=0.743966766 threshold failure remains valid and is marked `LEGACY_SINGLE_THRESHOLD_BORDERLINE`. V2 does not establish that it was “mis-killed”: only a single working point survives; unknown semantics, route-coordinate proof, route-tube evidence, and physical budget remain unresolved. Result R1/N1/query-compatible.
- **ARKitScenes M1 SplaTAM:** the legacy formal failure remains valid. The frozen 11-point curve supports R2 reconstruction-candidate evidence and diagnostic missingness, but no legal route/robot contract/runtime unknown/physical budget supports navigation. Result R2/N0/query-compatible; limited navigation is not evaluable.
- **TUM SplaTAM:** geometry/query evidence is separated from historical navigation progress failure. Numeric native/common parity and G0 do not supply independent full-scene reference, route, robot, unknown, or budget closure. Result R1/N0/query-compatible.
- **TUM Gaussian-SLAM:** adapter semantics, numeric parity, far-range historical geometry, and G0 are recorded independently from navigation. Missing route/reference/unknown/budget closure caps it at R1/N0/query-compatible.

## Allowed and forbidden claims

### REPLICA_GT_FINE

Allowed: immutable map-instance evidence; static query compatibility when true; reference-bounded reconstruction diagnostics; limited-domain navigation qualification under the frozen PR #64 contract.

Forbidden: algorithm stability; universal numeric qualification; full-space completeness from camera rays; navigation safety from G0 alone; legacy result overturned.

### REPLICA_SPLATFACTO

Allowed: immutable map-instance evidence; static query compatibility when true; reference-bounded reconstruction diagnostics.

Forbidden: algorithm stability; universal numeric qualification; full-space completeness from camera rays; navigation safety from G0 alone; legacy result overturned.

### TUM_SPLATFACTO_NEGATIVE

Allowed: immutable map-instance evidence; static query compatibility when true; reference-bounded reconstruction diagnostics.

Forbidden: algorithm stability; universal numeric qualification; full-space completeness from camera rays; navigation safety from G0 alone; legacy result overturned.

### REPLICA_SPLATAM_60

Allowed: immutable map-instance evidence; static query compatibility when true; reference-bounded reconstruction diagnostics.

Forbidden: algorithm stability; universal numeric qualification; full-space completeness from camera rays; navigation safety from G0 alone; legacy result overturned.

### ARKITSCENES_M1_SPLATAM

Allowed: immutable map-instance evidence; static query compatibility when true; reference-bounded reconstruction diagnostics.

Forbidden: algorithm stability; universal numeric qualification; full-space completeness from camera rays; navigation safety from G0 alone; legacy result overturned.

### TUM_SPLATAM_FORMAL

Allowed: immutable map-instance evidence; static query compatibility when true; reference-bounded reconstruction diagnostics.

Forbidden: algorithm stability; universal numeric qualification; full-space completeness from camera rays; navigation safety from G0 alone; legacy result overturned.

### TUM_GAUSSIAN_SLAM

Allowed: immutable map-instance evidence; static query compatibility when true; reference-bounded reconstruction diagnostics.

Forbidden: algorithm stability; universal numeric qualification; full-space completeness from camera rays; navigation safety from G0 alone; legacy result overturned.

### SAFER_OFFICIAL_FLIGHT

Allowed: immutable map-instance evidence; static query compatibility when true; reference-bounded reconstruction diagnostics.

Forbidden: algorithm stability; universal numeric qualification; full-space completeness from camera rays; navigation safety from G0 alone; legacy result overturned.

### SAFER_OFFICIAL_OLD_UNION2

Allowed: immutable map-instance evidence; static query compatibility when true; reference-bounded reconstruction diagnostics.

Forbidden: algorithm stability; universal numeric qualification; full-space completeness from camera rays; navigation safety from G0 alone; legacy result overturned.

### SAFER_OFFICIAL_STATUES

Allowed: immutable map-instance evidence; static query compatibility when true; reference-bounded reconstruction diagnostics.

Forbidden: algorithm stability; universal numeric qualification; full-space completeness from camera rays; navigation safety from G0 alone; legacy result overturned.

### SAFER_OFFICIAL_STONEHENGE

Allowed: immutable map-instance evidence; static query compatibility when true; reference-bounded reconstruction diagnostics.

Forbidden: algorithm stability; universal numeric qualification; full-space completeness from camera rays; navigation safety from G0 alone; legacy result overturned.

## Required 29-answer audit

1. Protocol V2 identity is byte-exact: `a0a02fd284c75c600095510899e2878f198d69ff088b66eccd3313275fdbde7e`.
2. PR #75 is the immutable upstream lineage; PR #68–#75 were not modified, and this report is a new V2 task classification.
3. The fixed inventory contains 11 maps: 6 accessible and 5 unavailable.
4. The controls passed: `PASS_PROTOCOL_V2_CONTROL_DISCRIMINATION`.
5. The positive control REPLICA_GT_FINE is R3/N3/query-compatible with frozen route, oracle, one-sided certificate and resolved budget.
6. REPLICA_SPLATFACTO remains R1/N1 despite query compatibility; TUM_SPLATFACTO_NEGATIVE remains historical negative evidence and is not executable.
7. Native/common status counts are {'NATIVE_ONLY': 1, 'NOT_EVALUABLE': 5, 'NUMERIC_PARITY_PASS': 2, 'SEMANTIC_PARITY_ONLY': 3}.
8. One complete frozen risk–coverage curve exists (ARKit M1); other learned evidence is single-point or unavailable.
9. One deterministic GT multi-tolerance certificate exists; no learned map has a complete new multi-tolerance evaluation.
10. One ARKit diagnostic missingness record is complete; no learned deployable runtime unknown model is established.
11. Only the GT control has a closed route-coordinate contract.
12. Only the GT control has a complete frozen route-tube evaluation.
13. Only the GT control has deterministic one-sided route-risk closure.
14. One physical budget is resolved and ten are unresolved.
15. Six maps completed G0 in 18 fresh processes; G0 affects query compatibility only.
16. Per-map R axes are listed in the classification table.
17. Per-map N axes are listed in the classification table.
18. Per-map query compatibility is listed independently in the classification table.
19. Per-map allowed and forbidden claims are listed above and serialized in the evidence cards.
20. Replica SplaTAM is not proven retrospectively qualified; its borderline legacy single threshold is not overturned.
21. ARKit M1 limited navigation is not evaluable under V2 because route, robot, runtime unknown and budget evidence are absent.
22. TUM geometry/query evidence is explicitly separated from navigation-protocol evidence.
23. No learned N3 map exists.
24. No learned N2 map exists.
25. No universal numeric gate is justified by current evidence.
26. Execution counts are frozen in run_manifest.json: `{"G0_processes": 18, "ICP_Sim3": 0, "N2_learned_maps": 0, "N3_learned_maps": 0, "artifact_unavailable": 5, "candidate_dependent_new_route_generation": 0, "checkpoint_resume": 0, "controller": 0, "download": 0, "frame_deletion": 0, "map_filtering": 0, "map_modification": 0, "multi_tolerance_evaluations": 1, "optimizer": 0, "planner_rollout": 0, "planner_search": 0, "risk_coverage_rerenders": 0, "risk_coverage_reused_complete_curves": 1, "route_tube_evaluations": 1, "scale_repair": 0, "training": 0}`.
27. FINAL_STATUS=NO_EXISTING_LEARNED_GAUSSIAN_MAP_NAVIGATION_QUALIFIED_UNDER_PROTOCOL_V2.
28. FINAL_DECISION=PROCEED_TO_NEW_DATASET_ENTRY_QUALIFICATION.
29. Only next task=ETH3D_DELIVERY_AREA_PROTOCOL_V2_ENTRY_QUALIFICATION_V1; ETH3D training remains unauthorized.

## Limitations and decision boundary

This is frozen-map-instance evidence, not algorithm-stability evidence. Five artifacts are unavailable, learned bidirectional multi-tolerance evidence is absent, route/budget/unknown closure is absent for every learned map, and pixels are not treated as independent replicates. These gaps are reported rather than filled by favorable assumptions. Consequently the preregistered tree selects Case C without a universal numeric gate.

## Traced outputs

Machine-readable results are in `run_manifest.json`, `validation_result.json`, the per-map evidence cards, classification matrix, and `eth3d_entry_handoff.json`. Twenty static figures distinguish measured, derived, empirical, unresolved, and not-evaluable evidence.
