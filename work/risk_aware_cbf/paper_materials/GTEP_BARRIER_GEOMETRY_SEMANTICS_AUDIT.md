# GTEP Barrier Geometry Semantics Audit

`GSplatLoader.query_distance` in [splat/gsplat_utils.py](../../../splat/gsplat_utils.py) implements the existing `ball-to-ellipsoid` safety query. For each Gaussian it rotates the position into that Gaussian's sorted-scale frame, solves for the closest ellipsoid surface point, transforms that point back to world coordinates, and returns `h = phi * squared_distance - (radius + epsilon)^2`.

The existing analytic position gradient is `grad_h = 2 * phi * (x - y)`, where `y` is that world-frame closest surface point. It is a position-only gradient, and CBF augments it with zero velocity components in [cbf/cbf_utils.py](../../../cbf/cbf_utils.py). Positive alignment with the normalized gradient is the local increasing-h direction.

The original recovery helper selects the critical Gaussian as `argmin(h)` in `query_h_and_critical` in `run_v4b_corrective_dt_filter.py`. The safety query returns all Gaussian constraints; the existing V4-C path uses the minimum. The GTEP adapter only delegates to this public analytic query, takes its minimum index, and has no state side effects. Multi-Gaussian aggregation was not run because the original local recovery contract does not expose a pre-registered top-k constraint/normal semantics.
