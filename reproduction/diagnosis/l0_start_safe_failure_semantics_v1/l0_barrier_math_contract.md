# Frozen L0 barrier math contract

## Inputs and representation

The L0 input is `payload.p_k`, copied from `state[:3]` at decision commit. In the frozen double-integrator runtime this is the three-dimensional robot position state, while `state[3:]` is velocity. L0 does not use the camera origin, the next state, the immediate segment, or candidate control. Evidence: `reproduction/instrumentation/l2_h1_on_policy_shadow_instrumentation_v1/immutable_payload.py:170-173` and `reproduction/equivalence/l2_h1_shadow_instrumentation_off_vs_on_v1/server_run_one.py:165-170`.

The map loader copies Gaussian means and quaternions from the frozen Nerfstudio checkpoint, exponentiates the stored log-scales exactly once, constructs covariance and inverse-covariance matrices, and also loads sigmoid opacities. Opacity is not consulted by the FULL barrier query. Evidence: `splat/gsplat_utils.py:31-40`.

## Exact computational graph

For query point `p` and Gaussian `i` with mean `mu_i`, rotation `R_i`, and positive principal scales `s_i`, the implementation:

1. sorts the scale axes and matching rotation columns;
2. computes local signed coordinates `q_i = R_i^T (p - mu_i) + 1e-8`;
3. solves the closest point `y_i` on the corresponding ellipsoid in the first octant;
4. computes squared clearance `d_i^2 = ||y_i - |q_i|||^2`;
5. sets `phi_i = sign(sum_j(q_ij / s_ij)^2 - 1)`;
6. computes `h_i = phi_i d_i^2 - r_eff^2`;
7. returns `h(p) = min_i h_i` through the adapter's `argmin` over the complete Gaussian array.

Source locations: `splat/gsplat_utils.py:162-185`, `splat/distances.py:96-130`, and `reproduction/cross_dataset/fas_cbf_unified_executable_safety_certifier_v1/adapters/gaussian_barrier_adapter.py:87-97`.

This is a signed **squared** clearance contract. The solver name/comment can suggest distance, but its returned value is explicitly `sum((y-x)^2)` and the query subtracts a squared radius, so there is no distance-versus-squared-distance mismatch in the executed expression.

## Radius and margin

The shadow contract records robot radius `0.10` and safety margin `0.01`, combines them upstream into `effective_radius=0.11`, and passes that single number to the source query. The source query uses its default `epsilon=0` and subtracts `(radius + epsilon)^2` exactly once. Gaussian scales define the base ellipsoid and are not separately inflated. Evidence: `server_run_one.py:101-103,125-127,165-170`, adapter line 87, and `splat/gsplat_utils.py:185`.

Thus shadow L0 uses an inflation component of `0.11^2 = 0.0121`. No double inflation is present in the L0 path.

## Zero level and sign

- `h > 0`: the minimum signed squared clearance is greater than `r_eff^2`; the point is outside every radius-inflated represented ellipsoid.
- `h = 0`: contact with the zero level of the radius-inflated represented set.
- `h < 0`: inside a represented ellipsoid or within `r_eff` of at least one represented ellipsoid.

For finite query output, frozen status mapping is `h>=0 -> PASS`, `h<0 -> FAIL`; this matches the formula's sign. Nonfinite arrays are mapped to `UNKNOWN`, not `FAIL`.

## Units

`p_k`, Gaussian means, and Gaussian scales share the frozen map/runtime coordinate system. Their base unit is the map coordinate unit; the frozen authority contract labels robot radius and margin in metres. Therefore `d_i` is in map metres and `h_i` in square metres under that authority. No state-to-map scaling or coordinate transform occurs in either the L0 or controller query path.
