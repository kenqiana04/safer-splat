# Reference role boundary

- `scan_eval + official evaluator + occlusion` is the R-axis authority.
- Rendered depth is an observable-ray evaluation oracle only.
- `scan_clean + alignment + verified occlusion mesh/splats` is only a future route/collision-oracle candidate.
- `scan_eval` is not a full-space route oracle because its support is restricted by official multi-view observability.
- No reference asset may be mounted under `TRAIN_INPUT_ROOT` or influence pruning, scale correction, split choice, or training.
