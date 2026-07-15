# TUM Remaining G0 Checkpoint-Entry Audit V1

This directory is a read-only evidence audit for the frozen `tum_metric_candidate`.
It is scoped to the remaining data, metric-coordinate, integrity, Nerfstudio
data-contract, and Splatfacto command-entry questions. It is not a training,
checkpoint-generation, SAFER loading, navigation, or G1 evaluation directory.

The audit is staged. `G0_PROTOCOL_PREREGISTRATION.md` and
`G0_GATE_REGISTRY.json` are committed before any RGB, depth, transform, or
dataparser inspection. Later artifacts record either observed evidence or an
explicit blocker; they must never modify source assets.

All new artifacts and scripts for this task are confined to this directory.
The Freeze V1 evidence under `reproduction/experiment_protocol_freeze_v1/` is
read-only.
