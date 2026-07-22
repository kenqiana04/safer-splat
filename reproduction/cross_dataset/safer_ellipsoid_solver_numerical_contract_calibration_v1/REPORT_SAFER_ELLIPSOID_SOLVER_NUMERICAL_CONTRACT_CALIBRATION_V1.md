# SAFER Ellipsoid Solver Numerical Contract Calibration V1

## Result

`BLOCKED_BY_DOWNSTREAM_GRADIENT_CONTRACT_UNRESOLVED`

The query/state gradient contract is calibrated as CASE A,
`OFFICIAL_ANALYTICAL_ENVELOPE_GRADIENT`. The live CBF QP also consumes
`hess_h`, which this task did not qualify. The protocol consequently forbids
calibrated static real-map audit, G0, and G1. No controller, dynamics, QP,
trajectory, navigation, SAFER rollout, G1, formal training, or V1R7 executed.

## Frozen basis

PR #41 was Open Draft at `5aefe713fd44b430489c64f4a8e752c5abc883e1`.
The raw Git blobs used were `distances.py`
`81940ca59297a2ee3b4214901b038725c2748318` and `gsplat_utils.py`
`4e704349ddb5b5d6737e38d63965699ecfe81030`. The shared server checkout did
not match them, so the tests imported `git cat-file blob` exports, never the
checkout files. No map or canonical array was modified.

## Mathematical and numerical evidence

The KKT condition for the constrained projection gives
`y_i=a_i^2 x_i/(lambda+a_i^2)`. On the regular domain, envelope/Danskin gives
`grad d2=2(x-y*)`, thus `grad h=2 phi (x-y*)`. This is a value-function
derivative, whereas unrolled reverse mode differentiates a finite branchy
program and need not agree.

Independent float64 KKT bisection and safeguarded Newton agreed on all 4,096
fixed synthetic cases: h max difference `9.33e-15`, y max `5.51e-14 m`,
gradient max `1.10e-13`, surface residual `2.43e-12`, KKT residual
`3.83e-16`. Fixed five-point FD was stable on all 4,096 cases; envelope-vs-FD
error was median `1.14e-10`, p99 `3.98e-10`, max `1.22e-9`.

Official float32 25-step forward passed: h error median `1.61e-8`, p99
`8.39e-8`, max `1.30e-7`; projection error median `7.25e-9`, p99 `2.76e-8`,
max `4.46e-8`. Its analytical gradient passed: finite ratio 1.0, error median
`1.61e-8`, p99 `4.05e-8`, max `6.27e-8`, cosine minimum
`0.9999999999996463`, directional p99 `5.74e-8`, max `1.09e-7`.

The finite-unrolled gradient failed the identical gate: error median
`1.34e-2`, p99 `6.68e-2`, max `1.09`, cosine minimum `-0.1332`, and one
reversed direction. A 1,024-case iteration diagnostic shows forward/envelope
errors settle near `1.6e-8` at 25 iterations but unrolled error remains near
`1.33e-2`. That is not a PyTorch defect. The separate edge registry contains
40 input-defined nonsmooth or extreme cases and is not mixed into statistics.

## Downstream boundary and next task

`CBF.get_QP_matrices` consumes `h`, `grad_h`, and `hes_h` in second-order Lie
derivative terms (`cbf/cbf_utils.py:45-63`). It does not require gradients to
map parameters, but it does require the unqualified Hessian. The task-owned
SplaTAM static process was stopped before a result; Gaussian-SLAM static was
not started. Thus no real active registry, static status, G0, primary-map, or
efficiency claim is made.

The next separately authorized task is `SAFER Ellipsoid Hessian Numerical
Contract Qualification V1`; only after that passes may static auditing or G1
be considered.
