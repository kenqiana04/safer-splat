# L2 predicate contract

Abstract interface only—no implementation is created:

`L2_H1_CERTIFY(x_k, u_k, expected_map_snapshot, frozen_segment_backend, frozen_robot_margin_contract) -> {PASS, FAIL, UNKNOWN}`

- `PASS`: the selected frozen formal backend returns `CERTIFIED_SAFE` with `certified=true` for all `alpha in [0,1]`.
- `FAIL`: a finite entire-segment evaluation returns `CERTIFIED_UNSAFE` and a witness.
- `UNKNOWN`: budget exhaustion, map UNKNOWN/NONFINITE/ERROR, snapshot mismatch, invalid input, unsupported backend, or any unclassified status.

Only the frozen `EXACT_ANALYTIC_SPHERE_SEGMENT_MINIMUM` or `CONSERVATIVE_SIGNED_DISTANCE_LIPSCHITZ_INTERVAL` may produce PASS. `DENSE_SAMPLED_DIAGNOSTIC_ONLY` and endpoint-only checks cannot. UNKNOWN fails closed but remains statistically distinct from candidate unsafe.
