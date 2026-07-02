# V4-A: Verified Active-Set Safe-Start Projection with Discrete-Time Safety Audit

## Why V4-A

Current StartGuard repair is effective on `flight100`, but it remains a heuristic multi-step repulsion procedure. For a stronger paper, safe-start repair should be formulated as a verified projection problem rather than only a repulsive displacement heuristic.

V4-A keeps the official SAFER-Splat baseline unchanged. It improves the reproduction layer under `work/risk_aware_cbf/` by adding:

- verified safe-start projection;
- an active-set / verify-expand search loop;
- full-query acceptance checks;
- log-only discrete-time safety verification.

## Safe-Start Projection Problem

Given an initial state `x0` and safety margin `delta`, find a nearby repaired state `x_safe`:

```text
minimize ||x_safe - x0||^2
subject to h(x_safe) >= delta under full GSplat safety query verification.
```

The implementation does not assume unavailable differentiable per-Gaussian projection formulas. Instead, it uses a black-box projection search:

1. Use the official GSplat safety query as verifier.
2. Use active nearby or violated Gaussian IDs only to seed directions and local search.
3. Search for a small displacement around the original start.
4. Verify each candidate using the full GSplat query.
5. Accept the minimum-distance candidate that passes the full-query margin.
6. If no candidate passes, expand active set or search radius.

## Active-Set / Verify-Expand Loop

1. Query `x_current`.
2. Extract nearest, most violated, or near-violated Gaussian IDs from available full-query safety values.
3. Build active set `A`.
4. Generate candidate repair directions from:
   - weighted repulsion;
   - nearest-Gaussian repulsion;
   - active-set repulsion directions;
   - coordinate directions;
   - fixed-seed random unit directions.
5. Evaluate candidates in increasing search radius.
6. Pick the candidate with minimum repair distance satisfying `h >= safety_margin` under full-query verification.
7. If no candidate passes, expand the active set, direction budget, or search radius.
8. Stop when:
   - verified `h >= safety_margin`;
   - repair distance exceeds `max_repair_distance`;
   - `max_projection_iterations` is reached.

The active set is a search accelerator and diagnostic object. It is not a replacement for full-query verification.

## Discrete-Time Safety Audit

This phase is log-only. Given executed control `u_t`:

1. Predict `x_{t+1}^{pred}` using the wrapper dynamics.
2. Query `h(x_{t+1}^{pred})`.
3. Compare with actual next recorded state `h(x_{t+1}^{actual})` when available.
4. Log:
   - `current_h`;
   - `predicted_next_h`;
   - `actual_next_h`;
   - `prediction_error_norm`;
   - `predicted_next_violation`;
   - `actual_next_violation`.
5. Do not modify the control in this phase.

## Claim Boundary

- No new CBF theorem is claimed.
- No official SAFER-Splat source is modified.
- `min_safety_h` is not meter clearance.
- Post-repair navigation is reported separately from original benchmark navigation.
- The projection result is full-query verified, but not claimed globally optimal.
