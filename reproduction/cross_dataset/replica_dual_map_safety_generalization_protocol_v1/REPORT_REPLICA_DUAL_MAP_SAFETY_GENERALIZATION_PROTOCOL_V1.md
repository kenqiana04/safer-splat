# Replica Dual-Map Safety Generalization Protocol V1

## Final status

`BLOCKED_BY_REPLICA_ROBOT_CONTRACT_AMBIGUITY`

## What was verified

The task began from PR #62 at `4e82ffc6de4d23ee9ef578f8740bfff1745b5708`: Open Draft, CLEAN, and still limited to `NO_ARKITSCENES_GS_TO_OFFICIAL_RGBD_FRAME_JOIN` / `CLOSE_PUBLIC_PRETRAINED_EXTERNAL_MAP_SEARCH`.  It added no data source, download, map payload, geometry processing, SAFER execution, or navigation.

Replica `apartment_0` V3 is internally consistent: its complete/content trees, protocol contract, selected-location registry, CSV manifest, transforms, pose array, raw `mesh.ply`, and Habitat navmesh all match the frozen SHA-256 identities recorded in `replica_dual_map_input_identity.json`.  The coordinate path is frozen metric Habitat Y-up to Nerfstudio OpenGL camera-to-world, with no normalization, automatic scale, ICP, Sim(3), or scale fitting.

The existing 60-frame SplaTAM map was recovered only by identity.  Its archived source commit is `da6bbcd24c248dc884ac7f49d62e91b841b26ccc`; its checkpoint, five canonical arrays, 2,135,123 Gaussian count, source configuration, pilot registry, and ingestion order are frozen in `frozen_splatam_map_identity.json`.  No Gaussian array was queried for qualification and the map was not modified.  The pre-existing global rendering conclusion remains exactly `SPLATAM_REPLICA_60_FRAME_PILOT_GEOMETRY_NOT_QUALIFIED`; this task did not revise it.

The SAFER authority is `f63b4c496861c4f8881348d74244c1ff9a528d51`, with all three required source blobs resolved.  No core file was modified.

## Blocking evidence

The highest-priority Stonehenge formal source (`run.py` at the frozen SAFER authority) uniquely fixes a 6D free-3D double integrator, forward-Euler `dt=0.05 s`, spherical `r_robot=0.015 m`, and `epsilon_base=0`.  It does **not** define a finite formal velocity bound or a finite formal bound on the actual QP output.  Its desired command is clipped componentwise to `[-0.1, 0.1]`, but the Clarabel QP has no box constraint and can return a different output.  A desired-command clip therefore cannot be substituted for `umax`.

Risk-Aware V1/bestD and the FAS-CBF frozen materials were checked at the next priority levels.  They record candidate/claim and discrete-time margins, not replacement finite `vmax`, `umax`, or a formal independent mesh-collision predicate.  The missing bounds make the required one-step reachable displacement and `rho_corridor` indeterminate.

The protocol explicitly requires the route registry and corridor to be frozen before reading any Gaussian map.  Consequently no route registry, corridor, mesh/ellipsoid distance engine, one-sided certificate, connectivity gate, G0, fallback profile, mesh collision oracle, selected map, or downstream benchmark handoff can be truthfully generated.

## Boundary accounting

All of the following are zero: external search, download, training/retraining, map modification, scale fitting, Sim(3), ICP, route generation, Gaussian distance queries, fallback profiles, controller/navigation/CBF-QP benchmarks, and TUM execution.  GPU 1 has no task-owned compute process.

The task-owned server preflight rechecked the V3 contract, raw mesh, and navmesh hashes and terminated with the expected `BLOCKED_BY_REPLICA_ROBOT_CONTRACT_AMBIGUITY` result (exit code 1).  Its report copy is `/disk1/zlab/maintenance_records/replica_dual_map_safety_generalization_protocol_v1/report/REPORT_REPLICA_DUAL_MAP_SAFETY_GENERALIZATION_PROTOCOL_V1.md`.

## Required resolution

Provide one versioned, authoritative Replica external-benchmark robot contract that specifies finite `vmax`, finite `umax` for the actual QP output, and an independent collision predicate; or explicitly authorize a new contract freeze.  Then the next run must begin with the same frozen V3 identities and create the deterministic route registry before accessing either Gaussian map.

No claim of a qualified external Gaussian safety map is made by this record.
