# TUM Dedicated RGB-D Gaussian Baseline Comparison V1

This task evaluates dedicated RGB-D Gaussian mapping baselines on the frozen
TUM `freiburg1_room` train/evaluation partition.  It is an external-baseline
comparison only: it neither creates a formal Splatfacto run nor enables
SAFER, navigation, G0, or G1.

## Frozen comparison contract

- Dataset: 300 RGB-D frames from the frozen processed TUM transform file.
- Train map construction: 240 frozen frames; held-out evaluation: the other
  60 frames.  The train/evaluation sets are disjoint and exhaustive.
- Geometry: metric depth only.  There is no scale fitting, Sim(3), or
  per-frame alignment.
- Pose policy: fixed dataset ground-truth poses.  Both external methods are
  therefore `MAP_ONLY_COMPARABLE`; tracking quality is intentionally excluded.
- Primary threshold: `delta1 >= 0.75`, unchanged from the frozen internal
  TUM gate.  A result without a verified common static adapter is never used
  as a G0-pass claim.

For SplaTAM, the held-out evaluation uses its official CUDA Gaussian
rasterizer and the native depth-plus-silhouette path; predicted depth is the
alpha-composited expected camera-z value.  Image metrics are computed from
that same native render.  The TUM dataset loader rebases its first pose, so a
single train-frame anchor is present only to preserve the map coordinate
origin and is excluded from all 60 metrics.

For Gaussian-SLAM, `tracking.odometry_type=gt` is an official config branch
whose tracker returns the supplied ground-truth pose.  Task-owned launchers
may disable logging and select the frozen input/output paths, but make no
mapping-core source edits.

## Evidence boundaries

Generated source, environment, dataset, run, and result summaries are compact
JSON evidence.  No external repository, environment, RGB-D image/depth data,
complete per-frame metric table, model checkpoint, or training log is tracked
in this repository.  The server remains the authoritative location for those
task-owned artifacts.

The common Gaussian adapter is deliberately a separate gate.  If coordinate
semantics, Gaussian parameter meaning, renderer assumptions, and normal/scale
handling are not jointly proven for an external method, it remains
`COMMON_ADAPTER_UNRESOLVED`; static SAFER/G0 checks are then not run and no
negative or positive controller conclusion is inferred.
