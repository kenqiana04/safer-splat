# TUM E3 Bounded Hyperparameter Sweep V1

This task is a pre-registered, single-seed, nonformal coordinate search over the
already qualified E3 source.  It is not a new method, a full hyperparameter
optimization, a statistical study, formal training, V1R7, navigation, a SAFER
rollout, controller/dynamics/CBF-QP execution, or G1.

The only mutable candidate fields are:

| Coordinate | Fixed values |
| --- | --- |
| Late depth-hold lambda | 0.20, 0.30, 0.40, 0.50 |
| Refinement lock step | 2000, 3000, 4000 |
| Depth Smooth-L1 beta (m) | 0.05, 0.10, 0.20 |

The search is sequential, not Cartesian: Round A ranks four lambda candidates;
Round B uses the selected lambda and ranks lock steps; Round C uses both selected
coordinates and ranks beta values.  Duplicate parameter settings are reused, so
there can be at most eight unique fresh 6000-step runs.  At most one selected
candidate can receive one independent fresh 10000-step run.  No 6000-step
checkpoint may be resumed or used as a load target.

All candidates use the immutable E3 source digest
`96d1fe63019f04824c9dc4949f91d30627344bb8de05cd62ae3d33c2f3944947`, seed
`20260716`, frozen V1R6 input identity, 300-frame TUM split, metric-seed asset,
raw metric depth comparison, and the validated GPU-1 runtime overlays.

Final classification is limited to the protocol gates recorded in the generated
report.  A stronger depth metric is not a safety proof, and static `h` remains a
repository safety value rather than metre clearance.
