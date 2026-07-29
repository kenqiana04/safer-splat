# Replica bounded direct-goal GT Gaussian map V1

## 1. Why PR #63 was blocked
PR #63 correctly retained BLOCKED_BY_REPLICA_ROBOT_CONTRACT_AMBIGUITY; it was not a failed experiment.

## 2. Why desired-command clip is not an actual bound
The nominal u_des clip cannot prove actual feasible control. The same QP contains explicit u and next-velocity box rows; infeasibility returns no control and no plant step.

## 3. Why this is a new contract
Authority is EXPLICIT_USER_AUTHORIZED_BENCHMARK_DESIGN and NEW_VERSIONED_REPLICA_BENCHMARK_DESIGN_CHOICE, not a recovered official SAFER robot contract.

## 4. Benchmark parameters and units
State=['px', 'py', 'pz', 'vx', 'vy', 'vz']; control=['ax', 'ay', 'az']; metric free-3D; forward Euler; dt=0.05 s; max steps=500; maximum simulation time=25.0 s; position/velocity success tolerance=0.03.

## 5. Bounded QP matrix
Raw CBF rows A_cbf u <= b_cbf are augmented with Iu<=umax, -Iu<=umax, dt Iu<=vmax-v, and -dt Iu<=vmax+v. Clarabel is authoritative float64.

## 6. Velocity invariance
Componentwise vmax=0.10 m/s and umax=0.10 m/s2. Two fresh 10,000-fixture validations passed with zero post-QP clipping and zero infeasible fallback to u_des.

## 7. Collision oracle
Full visual-mesh float64 BVH: point brute-force disagreement=0.0 m; continuous segment disagreement=0.0 m; no simplification or semantic-mesh substitution.

## 8. Why navmesh path is absent
The direct-goal controller uses only the frozen straight segment. navmesh is identity/diagnostic only; navmesh controller-path count=0.

## 9. Route registry and strata
Mesh-only registry froze 100 routes from 430 candidate pairs. Candidate strata={"MODERATE_LONG": 54, "MODERATE_MEDIUM": 20, "MODERATE_SHORT": 14, "OPEN_LONG": 94, "OPEN_MEDIUM": 50, "OPEN_SHORT": 46, "TIGHT_LONG": 8, "TIGHT_MEDIUM": 4, "TIGHT_SHORT": 3}.

## 10. Start-Safe registry
The mesh-only diagnostic registry contains 30 states: NEAR_SAFE=10, CONTACT=10, UNSAFE=10.

## 11. Why conservative surface-voxel Gaussians
Full-mesh triangle/AABB SAT avoids per-triangle Gaussian explosion while retaining a deterministic, route-independent safety geometry construction.

## 12. Coverage mathematics
Every closed mesh primitive intersects a closed voxel and each Gaussian sphere contains its full voxel cube. All vertices, centroids, edge midpoints and 1,000,000 area-weighted samples had zero uncovered points.

## 13. Three fixed profiles
COARSE: voxel=0.08 m; gaussians=139674; payload=11174400 B; coverage=PASS; free-space=FAIL; retained=0.82; intrusion p95/p99/max=0.041003/0.046316/0.056760 m.
MEDIUM: voxel=0.04 m; gaussians=568364; payload=45469600 B; coverage=PASS; free-space=FAIL; retained=0.91; intrusion p95/p99/max=0.022027/0.025826/0.029725 m.
FINE: voxel=0.02 m; gaussians=2285656; payload=182852960 B; coverage=PASS; free-space=PASS; retained=0.99; intrusion p95/p99/max=0.011939/0.014149/0.016593 m.

## 14. Resource gate
All three builds had positive finite arrays, normalized quaternions, duplicate voxel count zero, source primitive loss zero, and count below 2,500,000. No fourth profile was created.

## 15. Free-space intrusion
Intrusion is max(0, d_mesh-d_G). COARSE and MEDIUM are retained as failed free-space evidence; FINE intrusion p95/p99/max is 0.011939/0.014149/0.016593 m.

## 16. Route retention
FINE retained 99/100 routes (formal 0.9875); TIGHT/MODERATE/OPEN were {"MODERATE": {"retained": 43, "retained_ratio": 1.0, "total": 43}, "OPEN": {"retained": 42, "retained_ratio": 1.0, "total": 42}, "TIGHT": {"retained": 14, "retained_ratio": 0.9333333333333333, "total": 15}}. No route was deleted.

## 17. SAFER static G0
Three fresh FINE static GPU repeats passed: median=0.088314 s, p95=0.370015 s, peak=359009792 B, repeatable active index and no map mutation. Four-scene official slowest=22.893854 s; 2x limit=45.787708 s.

## 18. Selected map
FINE is the only selected profile and its role is CERTIFIED_GT_GEOMETRY_DERIVED_GAUSSIAN_SAFETY_MAP. Canonical asset tree SHA=3b318a98a454ec5c36410b3c41dfb3dd4a25b7b5a1899f1f2c939fbf24ad0e55.

## 19. It is not learned 3DGS
The map is not learned, not reconstructed 3DGS, and not evidence of mapping-frontend generalization; its primitives are deterministic conservative safety geometry.

## 20. Risk-Aware claim limit
No Risk-Aware navigation outcome is claimed. Future comparison may evaluate Risk-Aware V1 only under the same frozen bounded contract.

## 21. Controller/oracle separation
The selected canonical Gaussian map is the controller geometry input; the official mesh oracle is independent evaluation only. mesh-oracle controller input count=0.

## 22. No formal benchmark was run
Formal multi-step controller/navigation count=0. This task ran static map, G0 and one-step QP evidence only.

## 23. Mandatory learned external-map phase
SCANNETPP_LEARNED_3DGS_EXTERNAL_QUALIFICATION_V1 remains mandatory for paper-level learned external 3DGS validation; Replica GT-derived geometry does not replace it.

## 24. Final status
PASS_REPLICA_BOUNDED_DIRECT_GOAL_GT_GAUSSIAN_MAP_READY

## 25. Final decision
RUN_BOUNDED_REPLICA_SAFER_FAS_CBF_BENCHMARK

## 26. Only next task
RUN_REPLICA_BOUNDED_DIRECT_GOAL_SAFER_FAS_CBF_BENCHMARK_V1
