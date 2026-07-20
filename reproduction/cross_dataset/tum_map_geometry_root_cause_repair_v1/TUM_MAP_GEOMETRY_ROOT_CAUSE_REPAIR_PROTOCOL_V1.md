# TUM Map Geometry Root-Cause and Repair Protocol V1

This tracked protocol records a nonformal diagnosis of the V1R6 TUM map.  It
preserves V1R6, its data and its environment.  All derived artifacts are under
`/disk1/zlab/maintenance_records/tum_map_geometry_root_cause_repair_v1`.

The tested method family is deliberately distinct from V1R6: deterministic
metric RGB-D seed points and a fixed metric Smooth-L1 depth term (lambda 0.10,
beta 0.10).  It is not a retry, resume, V1R7, formal training run, navigation,
or G1 authorization.

Selection used all 60 fixed evaluation frames, raw metric depth only, no
Sim(3), global scale fitting, per-frame scale fitting, or frame filtering.
