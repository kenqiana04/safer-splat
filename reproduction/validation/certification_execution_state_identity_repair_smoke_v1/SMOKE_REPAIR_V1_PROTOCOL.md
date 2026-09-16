# Certification–Execution State Identity Repair Smoke Protocol V1

Role: `ENGINEERING_ACTIVE_RUNTIME_SMOKE_FOR_CERT_EXEC_IDENTITY_REPAIR_V1`.

This protocol freezes a post-repair engineering smoke for trials `15, 45, 75`, in that order, with at most 500 completed public cycles per trial. Trials are serial and isolated in separate processes under seed 0 and physical GPU1. The future run must use the repaired stack factory at implementation authority `546598a70e12fa99f9153f1927d0542ca27862b4`.

The smoke evaluates runtime composition, bitwise certification–execution continuity, typed mismatch fail-closure, canonical L1/L2/L3/backup/terminal lineage, trace cardinality, evidence completeness, and absence of policy/geometry drift. A boundary cycle has exactly one trace and zero PlantCommit; therefore PlantCommit count is not required to equal cycle count.

The future result root is `/disk1/zlab/v3_repair_records/cert_exec_identity_repair_smoke_v1_20260916`. First launch requires that root to be absent. The launcher performs CPU preflight and validation before creating it. The parent alone owns the root; `--one` requires a short-lived authorization bound to parent PID, result root, branch, source HEAD, protocol and lock hashes, trial ID, and secret-token hash. Any child failure stops the batch, persists evidence under `parent_failures/trial_<id>/`, and is never retried automatically.

The 0.015 q hard radius, zero margin, zero `rho_seg`, controller/routing/dynamics, and the repaired canonical float32 transition are immutable. The 0.025 q historical shell has zero runtime authority. No epsilon or tolerance is allowed for identity matching.

This is not a scientific efficacy experiment. It has no Reference arm, paired analyzer, collision/progress gate, Official100, Formal arm, population claim, deployment claim, or hard-real-time claim. The frozen scientific decision remains `FAIL_V3_HARD_SAFETY_GATE` regardless of smoke outcome.
