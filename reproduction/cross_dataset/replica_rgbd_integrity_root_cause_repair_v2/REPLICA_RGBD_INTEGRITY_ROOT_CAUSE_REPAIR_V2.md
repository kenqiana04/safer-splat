# Replica RGB-D Integrity Root-Cause, Qualified Repair and Atomic Publication V2

This task starts from the preserved `G0.5E-v1` failure evidence, not from a
new camera protocol. The immutable input is `apartment_0`, the 300-row camera
manifest with SHA-256 `1056121e4470124e180a3367172440f540f0acdc5adab665c3187ac8ab87be25`,
and the V1 checker recovered from historical blob
`cae67b3be07c1b801dc7af51ebc0ffcc6bbe6efb`.

The task-owned runner first inventories V1 read-only, reproduces its exact
thresholds, freezes the diagnostic registry, then compares one long-lived
serial simulator with two fresh-process/fresh-simulator repetitions per probe.
It permits a single full 300-frame V2 render only after a unique authorized
cause and its matching repair contract pass. No TUM rollout, Gaussian training,
SAFER/CBF/navigation execution, scene change, pose change, resampling, or V1
staging mutation is part of this task.

Final gate: `BLOCKED_BY_REPLICA_SCENE_ASSET_RENDER_COVERAGE_DEFECT`. Fresh
per-frame A/B observations reproduce the same frozen-frame failures, so V2
rendering and publication are intentionally not authorized.

Historical renderer, generator, validator, raw-closure and import source blob
identities are recorded in `historical_replica_source_identity.json`. The
task-owned implementation in `replica_v2_pipeline.py` preserves the historic
sensor and save semantics where they are not the diagnosed defect.
