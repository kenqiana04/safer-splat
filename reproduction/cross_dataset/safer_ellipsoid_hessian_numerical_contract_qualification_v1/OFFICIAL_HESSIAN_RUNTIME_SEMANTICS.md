# Frozen official Hessian runtime semantics

`distance_point_ellipsoid` computes a local ellipsoid-frame Hessian. Its diagonal uses `1-y/x`, algebraically `lambda/(lambda+a^2)` under the same KKT solution. `GSplatLoader.query_distance` rotates a world query into the gathered/sorted local rotation, computes local Hessian, multiplies it by `phi`, and returns it without `R @ H @ R.T`. In contrast, `grad_h` is reconstructed from world `x-y`. Hence returned `hess_h` is local while its CBF consumer requires world coordinates.

The targeted zero-component case also shows `y/x` can be nonfinite when the added `1e-8` exactly cancels a negative local component. A stable formula must avoid this division.
