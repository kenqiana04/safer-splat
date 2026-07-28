# Replica Scene Asset Geometry, Culling, Material and Render-Coverage Audit V1

This controlled protocol audits the frozen `apartment_0` V1 source asset without
changing the V1 staging tree, camera manifest, pose, rendering parameters, data
publication state, or any mapping/safety/TUM workflow.

The only permitted rendering is the pre-budgeted, fresh-process diagnostic set.
Every variant is server-only and carries `DIAGNOSTIC_ONLY_NOT_A_FORMAL_REPLICA_ASSET`.
The independent coverage reference is a task-owned CPU float64 BVH implementation
with a brute-force float64 Moller-Trumbore check on frozen key rays.
