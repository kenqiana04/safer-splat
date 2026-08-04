# Train One ETH3D 3DGS Map and Run FAS-CBF Module Stress Benchmark V1

## Scope recenter

PR #79 remains valid: ETH3D Delivery Area failed the frozen planner-coupled blocked-straight-line route-composition contract. This task does not overturn that result. It assigns the orthogonal role `LOCAL_SAFETY_AND_CONTROLLER_STRESS_BENCHMARK`, using one fixed learned Gaussian map as a controller experiment carrier with no global-planner or deployment-certification claim.

## Frozen identities and counts

- Base: PR #79 at `4694a7cbfa062a53ac270c1c1c5654a2d1b5f166`.
- Protocol V2: `a0a02fd284c75c600095510899e2878f198d69ff088b66eccd3313275fdbde7e`.
- Split: `dc6729a60e0f2971cb671e30bcce3a04adcd8f99298395d42f21855d666cc435`.
- TRAIN-only COLMAP tree: `5b0002cbdd4dff8985574c8f5d61640e9535709634959327e3b705794830b478`.
- Independent reference surface: `82a9b20c9f3c7dc933f86c45e0855adf649fcf08b7549baba760cf385d489370`.
- Official 3DGS source: `54c035f7834b564019656c3e3fcc3646292f727d`.
- Dataset/scene/input split/frontend/formal seed/formal map: exactly one each.
- Mapper sweeps, new mapping baselines, filtering, ICP/Sim3, scale repair, and frame deletion: zero.

## Map contract

The only frontend is official graphdeco-inria COLMAP RGB-only 3DGS. Smoke uses 500 iterations. The only formal map uses seed `20260804`, official default loss/densification, 30,000 iterations, and checkpoint markers 7,000/15,000/30,000. It may resume only the same initialized attempt after infrastructure interruption. TRAIN may not read heldout, guard, DSLR, depth, scan, mesh, or occlusion inputs.

The iteration-30,000 export is unfiltered and contains means, scales, rotations, opacity, and SH/color in the frozen metric frame. Three fresh export identities must match. Map-quality measurements are descriptive; only empty/nonfinite/wrong-frame/unrenderable/nondeterministic/leaking/oracle-unusable maps fail the minimum carrier gate.

## Controller benchmark contract

The registry is method-independent and targets 100 scenarios: 20 each for safe control, Start-Safe boundary, feasibility-dense, sampled-data gap, and predictive recovery. Ten per group is the minimum; fewer than 70 total yields activation-insufficient without changing the map or dataset.

The cumulative method matrix is SAFER baseline, Start-Safe only, Start-Safe plus Feasibility-Aware, plus discrete-time verification, and Full FAS-CBF with horizon-3 predictive recovery. Every method receives the same map, independent reference oracle, robot/dynamics, nominal controller, starts/goals, bounds, timestep, horizon, max steps, timeout, UNKNOWN policy, and logging. Reference geometry is evaluation-only and must never enter a controller decision.

Formal statistics use scenario as the unit. Module evidence is classified only as `SUPPORTED`, `PROMISING`, `NOT_SUPPORTED`, `REGRESSION`, or `INACTIVE` under the preregistered direction, bootstrap, activation, collision, progress, and feasibility rules. Smoothness and local-map confidence are diagnostics only; no adaptive margin, smoothness penalty, or rate constraint is introduced.

## Fail-closed decisions

- Case A: map viable, registry at least 70, no Full-FAS reference-collision regression, and at least two core modules supported/promising.
- Case B: map viable but stress activation insufficient; repair only the method-independent generator on the frozen map.
- Case C: module safety/progress/feasibility regression; preserve paired failures and debug the module without deleting cases or changing the map.
- Case D: catastrophic map viability failure; use the already-existing Replica GT and Replica SplaTAM maps, without searching a new dataset.

Allowed claims are limited to a paired, one-map, local controller robustness benchmark with independent reference evaluation. Deployment-certified map, N3, full SLAM, real-robot, mapper superiority, multi-seed stability, global navigation superiority, adaptive-margin completion, and smooth-controller completion claims are prohibited.
