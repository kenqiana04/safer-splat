# SAFER Ellipsoid Hessian Numerical Contract Qualification V1

## Result

`SAFER_ELLIPSOID_HESSIAN_MULTIPLE_CORRECTIONS_IDENTIFIED_CORE_PATCH_REQUIRED`

PR #42's query/state gradient CASE A remains frozen and valid. Hessian was the
remaining CBF blocker because `CBF.get_QP_matrices` uses `f.T @ H @ f` and
`g.T @ H @ f`. This task made no core modification.

## Frozen basis and reference

Base: PR #42 head `737f268a0a586063093729f3c71d6db164794c7f`. Raw blobs:
`distances.py` `81940ca59297a2ee3b4214901b038725c2748318`,
`gsplat_utils.py` `4e704349ddb5b5d6737e38d63965699ecfe81030`, and
`cbf/cbf_utils.py` `7c6e1300b125cc0a2a950ac2835a1fbe3d0de113`.

KKT gives `y_i=a_i^2u_i/(lambda+a_i^2)`,
`H_local=2 phi (I-J_y)`, and `H_world=R H_local R^T`. Independent float64
implicit-KKT and safeguarded-Newton/five-point envelope FD references agreed
on all 4,096 cases: normalized Frobenius median/p99/max
`5.03e-13 / 1.47e-12 / 2.37e-10`, FD stable `4096/4096`, and symmetry residual
`1.17e-15`.

## Coordinate frame

The registry has 512 identity, 128 each 90-degree X/Y/Z, and 3,200 general
rotations. Identity returned-Hessian median error is `2.37e-8`. Under general
rotations, returned Hessian matches local reference (median `2.35e-8`) but
fails world reference (median `8.37e-2`, p99 `0.529`, max `1.117`).
`R @ H_local @ R.T` restores world error to median `2.34e-8`, p99 `7.42e-8`,
max `2.52e-7`; its independent HVP p99/max are `7.21e-8 / 2.99e-7`.

`query_distance` rotates the query into the local frame and returns
`phi * hess` without rotating it back, while `grad_h` is world-frame. The
returned Hessian is therefore incompatible with downstream world-frame CBF.

## Stability

The official diagonal uses `1-y/x`. Of six retained near-zero cases, one
component became zero after the frozen `+1e-8` path: official finite ratio
`5/6`. The equivalent stable `lambda/(lambda+a^2)` was finite `6/6`. The
stable frozen-25-step world candidate passes regular synthetic gates: error
median/p99/max `2.09e-7 / 2.31e-4 / 3.69e-3`; HVP p99/max
`1.57e-4 / 7.32e-3`.

## Boundary and next step

CASE H-A did not occur. Real SplaTAM/Gaussian-SLAM cases, static reruns, G0,
primary map choice, and G1 are not run. `h` is signed squared distance, not
linear metre clearance. No controller, dynamics execution, QP, trajectory,
navigation, SAFER rollout, formal training, or V1R7 occurred.

The separately authorized next task is **SAFER World-Frame Stable Ellipsoid
Hessian Runtime Correction V1**: preserve h/gradient, replace `y/x`, return
`R @ H_local @ R.T`, then rerun all regressions before static or G1.
