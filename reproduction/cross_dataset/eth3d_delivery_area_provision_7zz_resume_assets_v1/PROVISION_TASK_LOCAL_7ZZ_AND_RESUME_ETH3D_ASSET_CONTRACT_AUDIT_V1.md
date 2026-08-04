# Provision Task-Local 7zz and Resume ETH3D Asset Contract Audit V1

This task continues Draft PR #78 at
`84126353999dc6af979f4d8533a5cbaf638895be`. It preserves the historical
`BLOCKED_BY_7Z_RUNTIME_UNAVAILABLE` evidence and resumes from
`PRE_DOWNLOAD_7Z_RUNTIME_GATE` only after a trusted task-local archive runtime
passes synthetic create/test/list/extract validation.

Scientific inputs and parameters are immutable: the nine/five archive
white/deny lists, Delivery Area scene, modality fallback rules,
`POSE_BLOCK_SPLIT_V1`, `ETH3D_MULTI_VIEW_FIRST_SURFACE_UNKNOWN_V1`, robot
dynamics, physical-budget equation, reference-only route rules, and Protocol V2
classification cannot be changed by infrastructure handling or observed data.

Infrastructure autonomy is limited to task-owned files, tools, downloads,
caches, processes, and the already-managed loopback reverse proxy. Training,
optimizer, smoke, learned-map generation, candidate-map access, controller runs,
ICP/Sim(3), scale repair, and frame deletion remain prohibited.

## Final scientific decision

The trusted task-local 7zz, all nine frozen official archives, split,
train-only COLMAP isolation, metric reference, ideal UNKNOWN support, and robot
budget gates passed. The corrected deterministic free-3D PRM produced 89,054
otherwise valid path candidates but zero reference-blocked start-goal straight
lines, below the frozen 50% planner-coupled quota. Therefore no route registry
was frozen and the task closed fail-closed with:

- `FINAL_STATUS=NO_ETH3D_DELIVERY_AREA_REFERENCE_ROUTE_BENCHMARK_CONTRACT`
- `FINAL_DECISION=CLOSE_ETH3D_DELIVERY_AREA_BEFORE_ENVIRONMENT_OR_TRAINING`
- `training_authorized=false`
- `Only next task=REVIEW_PROTOCOL_V2_REAL_WORLD_DATASET_ALTERNATIVES_V1`
