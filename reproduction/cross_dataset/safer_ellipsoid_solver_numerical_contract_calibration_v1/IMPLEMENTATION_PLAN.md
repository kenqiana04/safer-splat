# SAFER Ellipsoid Solver Numerical Contract Calibration V1 — Implementation Plan

1. Freeze the actual PR #41/server/map identities and recover the exact approved runtime invocation.
2. Implement independent float64 bisection and safeguarded-Newton references plus the fixed synthetic/finite-difference checks.
3. Compare official and exact-functional unrolled gradients under the pre-registered common contract; select only an allowed case.
4. Audit read-only downstream gradient/Hessian consumption and, only after a valid selection, rerun static-only calibrated map audits.
5. Write compact evidence/report artifacts, copy the report to the Desktop report directory, validate scope, commit, push, and open a Draft PR.

No controller, dynamics, QP, trajectory, navigation, SAFER rollout, G1, map modification, formal training, or V1R7 is authorized.
